from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.models import CandidateCluster, CategoryProposal
from synapsea.pipeline import SynapseaApp
from synapsea.review_queue import ReviewQueueRepository
from synapsea.storage import DecisionLogRepository
from synapsea.user_preferences import UserPreferencesRepository


class _StubInterpreter:
    def __init__(self, proposal: CategoryProposal) -> None:
        self._proposal = proposal

    def propose_category(self, cluster: CandidateCluster) -> CategoryProposal:
        return self._proposal

    def build_cluster_fingerprint(self, cluster: CandidateCluster) -> str:
        return cluster.cluster_id


class Milestone18PreferenceScoringTest(unittest.TestCase):
    def test_positive_preferences_raise_final_confidence(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            preferences = UserPreferencesRepository(root / "data" / "user_preferences.json")
            for _ in range(3):
                preferences.record_proposal_pair("documents::finance", accepted=True)
                preferences.record_token("invoice", "documents/finance", accepted=True)

            app = SynapseaApp(
                source_dir=root / "source",
                decision_log=DecisionLogRepository(root / "data" / "classification_log.db"),
                review_queue=ReviewQueueRepository(root / "data" / "review_queue.json"),
                user_preferences=preferences,
                proposal_interpreter=_StubInterpreter(
                    CategoryProposal(
                        should_create_category=True,
                        proposed_category="finance",
                        reason="test",
                        confidence=0.72,
                    )
                ),
            )
            cluster = CandidateCluster(
                cluster_id="cluster_001",
                parent_category="documents",
                file_count=3,
                dominant_extensions=[".pdf"],
                top_tokens=["invoice", "march"],
                pattern_signals={"dated_or_numbered": 1.0},
                example_files=["/tmp/a.pdf"],
                candidate_files=["/tmp/a.pdf", "/tmp/b.pdf"],
                heuristic_score=0.9,
                cluster_type="token_group",
            )

            app._refresh_review_queue([cluster])
            item = app.list_review_items()[0]

            self.assertEqual(item.base_confidence, 0.72)
            self.assertGreater(item.final_confidence, 0.72)
            self.assertEqual(item.confidence, item.final_confidence)
            self.assertTrue(item.preference_reasons)

    def test_negative_preferences_reduce_final_confidence(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            preferences = UserPreferencesRepository(root / "data" / "user_preferences.json")
            for _ in range(3):
                preferences.record_proposal_pair("documents::spam", accepted=False)

            app = SynapseaApp(
                source_dir=root / "source",
                decision_log=DecisionLogRepository(root / "data" / "classification_log.db"),
                review_queue=ReviewQueueRepository(root / "data" / "review_queue.json"),
                user_preferences=preferences,
                proposal_interpreter=_StubInterpreter(
                    CategoryProposal(
                        should_create_category=True,
                        proposed_category="spam",
                        reason="test",
                        confidence=0.85,
                    )
                ),
            )
            cluster = CandidateCluster(
                cluster_id="cluster_002",
                parent_category="documents",
                file_count=2,
                dominant_extensions=[".txt"],
                top_tokens=["spam"],
                pattern_signals={},
                example_files=["/tmp/a.txt"],
                candidate_files=["/tmp/a.txt"],
                heuristic_score=0.95,
                cluster_type="token_group",
            )

            app._refresh_review_queue([cluster])
            item = app.list_review_items()[0]

            self.assertLess(item.final_confidence, 0.85)
            self.assertIn("pair:", " ".join(item.preference_reasons))


if __name__ == "__main__":
    unittest.main()
