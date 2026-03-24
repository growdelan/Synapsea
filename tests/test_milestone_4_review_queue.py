from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.candidate_clusters import CandidateClusterRepository
from synapsea.cluster_engine import ClusterEngine
from synapsea.feature_extractor import FeatureExtractor
from synapsea.models import CategoryProposal
from synapsea.pipeline import SynapseaApp
from synapsea.review_queue import ReviewQueueRepository
from synapsea.storage import DecisionLogRepository


class FakeProposalInterpreter:
    def propose_category(self, cluster):
        token = cluster.top_tokens[0] if cluster.top_tokens else "group"
        return CategoryProposal(
            should_create_category=True,
            proposed_category=f"{token}_group",
            reason="Powtarzalny wzorzec klastrow.",
            confidence=0.9,
        )


class Milestone4ReviewQueueTest(unittest.TestCase):
    def test_run_once_saves_review_items_for_cluster_candidates(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_dir = root / "downloads"
            source_dir.mkdir()
            (source_dir / "Screenshot-2026-03-24.png").write_text("stub", encoding="utf-8")
            (source_dir / "Screenshot-2026-03-25.png").write_text("stub", encoding="utf-8")

            decision_log = DecisionLogRepository(root / "classification_log.db")
            cluster_repository = CandidateClusterRepository(root / "candidate_clusters.json")
            review_repository = ReviewQueueRepository(root / "review_queue.json")

            app = SynapseaApp(
                source_dir=source_dir,
                decision_log=decision_log,
                feature_extractor=FeatureExtractor(),
                cluster_engine=ClusterEngine(),
                candidate_clusters=cluster_repository,
                review_queue=review_repository,
                proposal_interpreter=FakeProposalInterpreter(),
            )

            app.run_once()

            review_items = review_repository.list_items()
            self.assertGreaterEqual(len(review_items), 1)
            self.assertEqual(review_items[0].status, "pending")
            self.assertTrue(review_items[0].proposed_category.endswith("_group"))
