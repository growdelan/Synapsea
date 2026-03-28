from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
from typing import Callable, Iterable

from synapsea.ai_state import AiProposalCacheRepository, DeferredClusterRepository
from synapsea.candidate_clusters import CandidateClusterRepository
from synapsea.classifier import FileClassifier
from synapsea.cluster_engine import ClusterEngine
from synapsea.config import AppConfig
from synapsea.evolution_engine import EvolutionEngine
from synapsea.feature_extractor import FeatureExtractor
from synapsea.input_state import InputStateRepository
from synapsea.learning import LearningSignalRepository, SnapshotRepository
from synapsea.models import (
    CandidateCluster,
    CategoryProposal,
    ClassificationDecision,
    FileFeatures,
    LearningSignal,
    ReviewItem,
    TaxonomyNode,
)
from synapsea.ollama_client import HttpOllamaTransport, OllamaClient
from synapsea.review_queue import ReviewQueueRepository
from synapsea.scanner import FileScanner
from synapsea.storage import DecisionLogRepository
from synapsea.taxonomy import TaxonomyRepository
from synapsea.user_preferences import PreferenceScoreBreakdown, UserPreferencesRepository


FileIterator = Callable[[], Iterable[Path]]


@dataclass(slots=True)
class ApplyMoveReport:
    moved: int = 0
    skipped: int = 0
    errors: int = 0


class SynapseaApp:
    def __init__(
        self,
        source_dir: Path,
        decision_log: DecisionLogRepository,
        classifier: FileClassifier | None = None,
        feature_extractor: FeatureExtractor | None = None,
        scanner: FileScanner | None = None,
        cluster_engine: ClusterEngine | None = None,
        candidate_clusters: CandidateClusterRepository | None = None,
        review_queue: ReviewQueueRepository | None = None,
        taxonomy: TaxonomyRepository | None = None,
        learning_signals: LearningSignalRepository | None = None,
        snapshot_repository: SnapshotRepository | None = None,
        evolution_engine: EvolutionEngine | None = None,
        input_state_repository: InputStateRepository | None = None,
        ai_proposal_cache: AiProposalCacheRepository | None = None,
        deferred_clusters: DeferredClusterRepository | None = None,
        user_preferences: UserPreferencesRepository | None = None,
        ai_budget_per_cycle: int = 20,
        proposal_interpreter: OllamaClient | None = None,
        iter_files: FileIterator | None = None,
    ) -> None:
        self.source_dir = source_dir
        self.decision_log = decision_log
        self.classifier = classifier or FileClassifier()
        self.feature_extractor = feature_extractor or FeatureExtractor()
        self.scanner = scanner or FileScanner()
        self.cluster_engine = cluster_engine or ClusterEngine()
        self.candidate_clusters = candidate_clusters
        self.review_queue = review_queue
        self.taxonomy = taxonomy
        self.learning_signals = learning_signals
        self.snapshot_repository = snapshot_repository
        self.input_state_repository = input_state_repository
        self.ai_proposal_cache = ai_proposal_cache
        self.deferred_clusters = deferred_clusters
        self.ai_budget_per_cycle = max(1, ai_budget_per_cycle)
        self.evolution_engine = evolution_engine or EvolutionEngine()
        self.proposal_interpreter = proposal_interpreter
        self.iter_files = iter_files or self._iter_source_files
        self.user_preferences = user_preferences

    @classmethod
    def from_config(cls, config: AppConfig) -> "SynapseaApp":
        decision_log = DecisionLogRepository(config.data_dir / "classification_log.db")
        candidate_clusters = CandidateClusterRepository(config.data_dir / "candidate_clusters.json")
        review_queue = ReviewQueueRepository(config.data_dir / "review_queue.json")
        taxonomy = TaxonomyRepository(config.data_dir / "taxonomy.json")
        learning_signals = LearningSignalRepository(config.data_dir / "learning_signals.json")
        snapshot_repository = SnapshotRepository(config.data_dir / "snapshot.json")
        input_state_repository = InputStateRepository(config.data_dir / "input_state.json")
        ai_proposal_cache = AiProposalCacheRepository(config.data_dir / "ai_proposal_cache.json")
        deferred_clusters = DeferredClusterRepository(config.data_dir / "deferred_clusters.json")
        user_preferences = UserPreferencesRepository(config.data_dir / "user_preferences.json")
        proposal_interpreter = None
        if config.enable_ai_review:
            proposal_interpreter = OllamaClient(
                HttpOllamaTransport(
                    endpoint=config.ollama_endpoint,
                    model=config.ollama_model,
                    timeout_seconds=config.ollama_timeout_seconds,
                ),
                max_examples=config.ai_max_examples,
            )
        return cls(
            source_dir=config.source_dir,
            decision_log=decision_log,
            candidate_clusters=candidate_clusters,
            review_queue=review_queue,
            taxonomy=taxonomy,
            learning_signals=learning_signals,
            snapshot_repository=snapshot_repository,
            input_state_repository=input_state_repository,
            ai_proposal_cache=ai_proposal_cache,
            deferred_clusters=deferred_clusters,
            user_preferences=user_preferences,
            ai_budget_per_cycle=config.ai_budget_per_cycle,
            proposal_interpreter=proposal_interpreter,
        )

    def run_once(self) -> int:
        previous_state = self.input_state_repository.load() if self.input_state_repository is not None else {}
        current_paths = self._collect_current_paths()
        current_state = self._build_input_state(current_paths)

        created_or_modified, deleted_paths = self._compute_delta(previous_state, current_state)
        impacted_categories: set[str] = set()
        if deleted_paths:
            for decision in self.decision_log.list_all():
                if decision.file_path in deleted_paths:
                    impacted_categories.add(decision.category)
            self.decision_log.remove_paths(sorted(deleted_paths))

        processed = 0
        for path in created_or_modified:
            decision = self.classifier.classify(self.extract_features(path))
            self.decision_log.record(decision)
            impacted_categories.add(decision.category)
            processed += 1

        self._capture_passive_learning(current_paths)
        self.refresh_candidate_clusters(impacted_categories)
        if self.input_state_repository is not None:
            self.input_state_repository.save(current_state)
        return processed

    def refresh_candidate_clusters(
        self,
        affected_categories: set[str] | None = None,
    ) -> list[ClassificationDecision]:
        decisions = self.decision_log.list_all()
        if affected_categories is not None and not affected_categories:
            if self.deferred_clusters is not None and self.deferred_clusters.load():
                if self.candidate_clusters is not None:
                    clusters = self.candidate_clusters.load()
                    self._refresh_review_queue(clusters)
            return decisions
        if self.candidate_clusters is not None:
            if affected_categories:
                affected_decisions = [d for d in decisions if d.category in affected_categories]
                rebuilt = self.cluster_engine.build_clusters(affected_decisions)
                existing = self.candidate_clusters.load()
                untouched = [cluster for cluster in existing if cluster.parent_category not in affected_categories]
                clusters = self._reindex_clusters([*untouched, *rebuilt])
            else:
                clusters = self.cluster_engine.build_clusters(decisions)
            self.candidate_clusters.save(clusters)
            self._refresh_review_queue(clusters)
            self._refresh_evolution_queue()
        return decisions

    def _refresh_review_queue(self, clusters: list[CandidateCluster]) -> None:
        if self.review_queue is None or self.proposal_interpreter is None:
            return

        deferred_ids = set(self.deferred_clusters.load()) if self.deferred_clusters is not None else set()
        eligible = [cluster for cluster in clusters if cluster.heuristic_score >= 0.7]
        prioritized = sorted(
            eligible,
            key=lambda item: (item.cluster_id not in deferred_ids, -item.heuristic_score),
        )
        limited = prioritized[: self.ai_budget_per_cycle]
        postponed = [cluster.cluster_id for cluster in prioritized[self.ai_budget_per_cycle :]]

        for index, cluster in enumerate(limited, start=1):
            if cluster.heuristic_score < 0.7:
                continue
            proposal = self._get_or_create_ai_proposal(cluster)
            if not proposal.should_create_category:
                continue
            breakdown = self._score_review_from_preferences(cluster, proposal)
            if breakdown.final_confidence < 0.7:
                continue
            review_item = ReviewItem.from_cluster(
                cluster=cluster,
                proposal=proposal,
                item_id=f"rev_{index:03d}",
            )
            review_item.base_confidence = breakdown.base_confidence
            review_item.preference_delta = breakdown.preference_delta
            review_item.final_confidence = breakdown.final_confidence
            review_item.preference_reasons = list(breakdown.reasons)
            review_item.confidence = breakdown.final_confidence
            self.review_queue.add_item(review_item)
        if self.deferred_clusters is not None:
            self.deferred_clusters.save(postponed)

    def _get_or_create_ai_proposal(self, cluster: CandidateCluster) -> CategoryProposal:
        if not hasattr(self.proposal_interpreter, "build_cluster_fingerprint"):
            return self.proposal_interpreter.propose_category(cluster)

        fingerprint = self.proposal_interpreter.build_cluster_fingerprint(cluster)
        if self.ai_proposal_cache is not None:
            cached = self.ai_proposal_cache.get(fingerprint)
            if cached is not None:
                return cached
        proposal = self.proposal_interpreter.propose_category(cluster)
        if self.ai_proposal_cache is not None:
            self.ai_proposal_cache.set(fingerprint, proposal)
        return proposal

    def _score_review_from_preferences(
        self, cluster: CandidateCluster, proposal: CategoryProposal
    ) -> PreferenceScoreBreakdown:
        target_path = f"{cluster.parent_category}/{proposal.proposed_category}"
        if self.user_preferences is None:
            return self._default_breakdown(proposal.confidence)
        return self.user_preferences.score_review_item(
            parent_category=cluster.parent_category,
            proposed_category=proposal.proposed_category,
            target_path=target_path,
            base_confidence=proposal.confidence,
            tokens=list(cluster.top_tokens),
            heuristics=[cluster.cluster_type] if cluster.cluster_type else [],
            patterns=list(cluster.pattern_signals.keys()),
        )

    def _default_breakdown(self, base_confidence: float) -> PreferenceScoreBreakdown:
        return PreferenceScoreBreakdown(
            base_confidence=base_confidence,
            preference_delta=0.0,
            final_confidence=base_confidence,
            reasons=[],
        )

    def _iter_source_files(self) -> Iterable[Path]:
        yield from self.scanner.scan(self.source_dir)

    def _collect_current_paths(self) -> list[Path]:
        current: list[Path] = []
        for path in self.iter_files():
            if isinstance(path, Path):
                current.append(path)
        return current

    def _build_input_state(self, paths: list[Path]) -> dict[str, dict[str, int]]:
        state: dict[str, dict[str, int]] = {}
        for path in paths:
            try:
                stat = path.stat()
                inode = int(stat.st_ino)
                size = int(stat.st_size)
                mtime_ns = int(stat.st_mtime_ns)
            except FileNotFoundError:
                inode = 0
                size = 0
                mtime_ns = 0
            state[str(path)] = {
                "inode": inode,
                "size": size,
                "mtime_ns": mtime_ns,
            }
        return state

    def _compute_delta(
        self,
        previous: dict[str, dict[str, int]],
        current: dict[str, dict[str, int]],
    ) -> tuple[list[Path], set[str]]:
        changed_paths: list[Path] = []
        for file_path, state in current.items():
            if previous.get(file_path) != state:
                changed_paths.append(Path(file_path))
        deleted = set(previous.keys()).difference(current.keys())
        return changed_paths, deleted

    def _reindex_clusters(self, clusters: list[CandidateCluster]) -> list[CandidateCluster]:
        reordered: list[CandidateCluster] = []
        for index, cluster in enumerate(
            sorted(clusters, key=lambda item: (item.parent_category, item.cluster_type, item.top_tokens)),
            start=1,
        ):
            reordered.append(
                CandidateCluster(
                    cluster_id=f"cluster_{index:03d}",
                    parent_category=cluster.parent_category,
                    file_count=cluster.file_count,
                    dominant_extensions=list(cluster.dominant_extensions),
                    top_tokens=list(cluster.top_tokens),
                    pattern_signals=dict(cluster.pattern_signals),
                    example_files=list(cluster.example_files),
                    candidate_files=list(cluster.candidate_files),
                    heuristic_score=cluster.heuristic_score,
                    cluster_type=cluster.cluster_type,
                )
            )
        return reordered

    def extract_features(self, path: Path) -> FileFeatures:
        return self.feature_extractor.extract(path)

    def list_review_items(self) -> list[ReviewItem]:
        if self.review_queue is None:
            return []
        return self.review_queue.list_items()

    def apply_review_item(self, item_id: str) -> tuple[ReviewItem, ApplyMoveReport]:
        if self.review_queue is None or self.taxonomy is None:
            raise RuntimeError("Brak skonfigurowanej review queue lub taksonomii.")
        item = self.review_queue.update_status(item_id, "applied")
        taxonomy = self.taxonomy.load()
        parent = taxonomy.get(item.parent_category)
        if parent is None:
            taxonomy[item.parent_category] = TaxonomyNode(children=[item.proposed_category], status="stable")
        else:
            children = list(parent.children)
            if item.proposed_category not in children:
                children.append(item.proposed_category)
            taxonomy[item.parent_category] = TaxonomyNode(children=children, status=parent.status)
        if item.proposed_category not in taxonomy:
            taxonomy[item.proposed_category] = TaxonomyNode(children=[], status="proposed")
        self.taxonomy.save(taxonomy)
        self._record_learning_signal(
            signal_type="review_applied",
            category=item.parent_category,
            file_path=item.target_path,
            details={"proposed_category": item.proposed_category},
        )
        self._learn_from_review_decision(item, accepted=True)
        move_report = self._move_candidate_files(item)
        return item, move_report

    def _move_candidate_files(self, item: ReviewItem) -> ApplyMoveReport:
        report = ApplyMoveReport()
        destination_dir = self.source_dir / item.target_path

        for candidate in item.candidate_files:
            source_path = Path(candidate)
            destination_path = destination_dir / source_path.name

            if not source_path.exists():
                report.errors += 1
                continue

            if destination_path.exists():
                report.skipped += 1
                continue

            try:
                destination_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source_path), str(destination_path))
                report.moved += 1
            except OSError:
                report.errors += 1
        return report

    def reject_review_item(self, item_id: str) -> ReviewItem:
        if self.review_queue is None:
            raise RuntimeError("Brak skonfigurowanej review queue.")
        item = self.review_queue.update_status(item_id, "rejected")
        self._record_learning_signal(
            signal_type="review_rejected",
            category=item.parent_category,
            file_path=item.target_path,
            details={"proposed_category": item.proposed_category},
        )
        self._learn_from_review_decision(item, accepted=False)
        return item

    def _learn_from_review_decision(self, item: ReviewItem, *, accepted: bool) -> None:
        if self.user_preferences is None:
            return

        pair_key = f"{item.parent_category}::{item.proposed_category}"
        self.user_preferences.record_proposal_pair(pair_key, accepted=accepted)
        if not accepted:
            return

        category_key = item.target_path
        tokens, heuristic_classes, pattern_keys = self._collect_item_signals(item)
        for token in tokens:
            self.user_preferences.record_token(token, category_key, accepted=True)
        for heuristic in heuristic_classes:
            self.user_preferences.record_heuristic(heuristic, category_key, accepted=True)
        for pattern in pattern_keys:
            self.user_preferences.record_pattern(pattern, category_key, accepted=True)

    def _collect_item_signals(self, item: ReviewItem) -> tuple[set[str], set[str], set[str]]:
        decision_by_path = {decision.file_path: decision for decision in self.decision_log.list_all()}
        tokens: set[str] = set()
        heuristics: set[str] = set()
        patterns: set[str] = set()

        for path in item.candidate_files:
            decision = decision_by_path.get(path)
            if decision is None:
                continue
            tokens.update(token for token in decision.tokens if len(token) >= 3)
            heuristics.update(decision.heuristic_classes)
            patterns.update(key for key, value in decision.pattern_signals.items() if value > 0.0)

        if not tokens:
            fallback_tokens = re.findall(r"[a-z0-9]+", item.proposed_category.lower())
            tokens.update(token for token in fallback_tokens if len(token) >= 3)

        if not heuristics and item.cluster_id:
            heuristics.add(f"cluster:{item.cluster_id}")
        return tokens, heuristics, patterns

    def _capture_passive_learning(self, current_paths: list[Path] | None = None) -> None:
        if self.snapshot_repository is None:
            return
        previous = self.snapshot_repository.load()
        current: dict[str, str] = {}
        for path in current_paths if current_paths is not None else self._iter_source_files():
            inode = str(path.stat().st_ino)
            current[inode] = str(path)
            old_path = previous.get(inode)
            if old_path and old_path != str(path):
                suggested_category = next(
                    (token for token in self.extract_features(path).tokens if len(token) >= 4),
                    path.stem.lower(),
                )
                self._record_learning_signal(
                    signal_type="manual_rename",
                    category=self.classifier.classify(self.extract_features(path)).category,
                    file_path=str(path),
                    details={"old_path": old_path, "suggested_category": suggested_category},
                )
        self.snapshot_repository.save(current)

    def _record_learning_signal(
        self,
        signal_type: str,
        category: str,
        file_path: str,
        details: dict[str, object],
    ) -> None:
        if self.learning_signals is None:
            return
        next_index = len(self.learning_signals.list_signals()) + 1
        self.learning_signals.add_signal(
            LearningSignal(
                signal_id=f"sig_{next_index:03d}",
                signal_type=signal_type,
                category=category,
                file_path=file_path,
                details=details,
            )
        )

    def _refresh_evolution_queue(self) -> None:
        if self.learning_signals is None or self.review_queue is None or self.taxonomy is None:
            return
        proposals = self.evolution_engine.build_proposals(
            signals=self.learning_signals.list_signals(),
            taxonomy=self.taxonomy.load(),
            start_index=len(self.review_queue.list_items()) + 1,
        )
        for proposal in proposals:
            self.review_queue.add_item(proposal)
