from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable

from synapsea.candidate_clusters import CandidateClusterRepository
from synapsea.classifier import FileClassifier
from synapsea.cluster_engine import ClusterEngine
from synapsea.config import AppConfig
from synapsea.feature_extractor import FeatureExtractor
from synapsea.models import CandidateCluster, ClassificationDecision, FileFeatures, ReviewItem
from synapsea.ollama_client import HttpOllamaTransport, OllamaClient
from synapsea.review_queue import ReviewQueueRepository
from synapsea.scanner import FileScanner
from synapsea.storage import DecisionLogRepository


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
        self.proposal_interpreter = proposal_interpreter
        self.iter_files = iter_files or self._iter_source_files

    @classmethod
    def from_config(cls, config: AppConfig) -> "SynapseaApp":
        decision_log = DecisionLogRepository(config.data_dir / "classification_log.db")
        candidate_clusters = CandidateClusterRepository(config.data_dir / "candidate_clusters.json")
        review_queue = ReviewQueueRepository(config.data_dir / "review_queue.json")
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
        self.refresh_candidate_clusters()
        return processed

    def refresh_candidate_clusters(self) -> list[ClassificationDecision]:
        decisions = self.decision_log.list_all()
        if self.candidate_clusters is not None:
            clusters = self.cluster_engine.build_clusters(decisions)
            self.candidate_clusters.save(clusters)
            self._refresh_review_queue(clusters)
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
