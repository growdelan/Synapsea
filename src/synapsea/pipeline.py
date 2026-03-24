from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable

from synapsea.candidate_clusters import CandidateClusterRepository
from synapsea.classifier import FileClassifier
from synapsea.cluster_engine import ClusterEngine
from synapsea.config import AppConfig
from synapsea.evolution_engine import EvolutionEngine
from synapsea.feature_extractor import FeatureExtractor
from synapsea.learning import LearningSignalRepository, SnapshotRepository
from synapsea.models import CandidateCluster, ClassificationDecision, FileFeatures, LearningSignal, ReviewItem, TaxonomyNode
from synapsea.ollama_client import HttpOllamaTransport, OllamaClient
from synapsea.review_queue import ReviewQueueRepository
from synapsea.scanner import FileScanner
from synapsea.storage import DecisionLogRepository
from synapsea.taxonomy import TaxonomyRepository


FileIterator = Callable[[], Iterable[Path]]


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
        self.evolution_engine = evolution_engine or EvolutionEngine()
        self.proposal_interpreter = proposal_interpreter
        self.iter_files = iter_files or self._iter_source_files

    @classmethod
    def from_config(cls, config: AppConfig) -> "SynapseaApp":
        decision_log = DecisionLogRepository(config.data_dir / "classification_log.db")
        candidate_clusters = CandidateClusterRepository(config.data_dir / "candidate_clusters.json")
        review_queue = ReviewQueueRepository(config.data_dir / "review_queue.json")
        taxonomy = TaxonomyRepository(config.data_dir / "taxonomy.json")
        learning_signals = LearningSignalRepository(config.data_dir / "learning_signals.json")
        snapshot_repository = SnapshotRepository(config.data_dir / "snapshot.json")
        proposal_interpreter = None
        if config.enable_ai_review:
            proposal_interpreter = OllamaClient(
                HttpOllamaTransport(
                    endpoint=config.ollama_endpoint,
                    model=config.ollama_model,
                )
            )
        return cls(
            source_dir=config.source_dir,
            decision_log=decision_log,
            candidate_clusters=candidate_clusters,
            review_queue=review_queue,
            taxonomy=taxonomy,
            learning_signals=learning_signals,
            snapshot_repository=snapshot_repository,
            proposal_interpreter=proposal_interpreter,
        )

    def run_once(self) -> int:
        processed = 0
        for path in self.iter_files():
            if not isinstance(path, Path):
                continue
            decision = self.classifier.classify(self.extract_features(path))
            self.decision_log.record(decision)
            processed += 1
        self._capture_passive_learning()
        self.refresh_candidate_clusters()
        return processed

    def refresh_candidate_clusters(self) -> list[ClassificationDecision]:
        decisions = self.decision_log.list_all()
        if self.candidate_clusters is not None:
            clusters = self.cluster_engine.build_clusters(decisions)
            self.candidate_clusters.save(clusters)
            self._refresh_review_queue(clusters)
            self._refresh_evolution_queue()
        return decisions

    def _refresh_review_queue(self, clusters: list[CandidateCluster]) -> None:
        if self.review_queue is None or self.proposal_interpreter is None:
            return
        for index, cluster in enumerate(clusters, start=1):
            if cluster.heuristic_score < 0.7:
                continue
            proposal = self.proposal_interpreter.propose_category(cluster)
            if not proposal.should_create_category or proposal.confidence < 0.7:
                continue
            review_item = ReviewItem.from_cluster(
                cluster=cluster,
                proposal=proposal,
                item_id=f"rev_{index:03d}",
            )
            self.review_queue.add_item(review_item)

    def _iter_source_files(self) -> Iterable[Path]:
        yield from self.scanner.scan(self.source_dir)

    def extract_features(self, path: Path) -> FileFeatures:
        return self.feature_extractor.extract(path)

    def list_review_items(self) -> list[ReviewItem]:
        if self.review_queue is None:
            return []
        return self.review_queue.list_items()

    def apply_review_item(self, item_id: str) -> ReviewItem:
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
        return item

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
        return item

    def _capture_passive_learning(self) -> None:
        if self.snapshot_repository is None:
            return
        previous = self.snapshot_repository.load()
        current: dict[str, str] = {}
        for path in self._iter_source_files():
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
