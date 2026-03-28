from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.config import AppConfig
from synapsea.models import CandidateCluster, CategoryProposal, ClassificationDecision
from synapsea.pipeline import SynapseaApp


class _StubInterpreter:
    def __init__(self, confidence: float) -> None:
        self._confidence = confidence

    def propose_category(self, cluster: CandidateCluster) -> CategoryProposal:
        return CategoryProposal(
            should_create_category=True,
            proposed_category="finance",
            reason="test",
            confidence=self._confidence,
        )

    def build_cluster_fingerprint(self, cluster: CandidateCluster) -> str:
        return cluster.cluster_id


class Milestone20PreferenceE2ETest(unittest.TestCase):
    def test_review_decision_updates_future_ranking(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_dir = root / "source"
            data_dir = root / "data"
            source_dir.mkdir(parents=True, exist_ok=True)
            data_dir.mkdir(parents=True, exist_ok=True)
            file_path = source_dir / "invoice_2026.pdf"
            file_path.write_text("invoice", encoding="utf-8")

            (data_dir / "review_queue.json").write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "id": "rev_apply",
                                "type": "create_category",
                                "status": "pending",
                                "confidence": 0.75,
                                "parent_category": "documents",
                                "proposed_category": "finance",
                                "target_path": "documents/finance",
                                "candidate_files": [str(file_path)],
                                "reason": "test",
                                "cluster_id": "cluster_apply",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (data_dir / "taxonomy.json").write_text("{}", encoding="utf-8")

            app = SynapseaApp.from_config(
                AppConfig(source_dir=source_dir, data_dir=data_dir, enable_ai_review=False)
            )
            app.decision_log.record(
                ClassificationDecision(
                    file_path=str(file_path),
                    category="documents",
                    reason="seed",
                    confidence=0.9,
                    extension=".pdf",
                    tokens=["invoice", "march"],
                    heuristic_classes=["document_like"],
                    pattern_signals={"dated_or_numbered": 1.0},
                )
            )
            app.apply_review_item("rev_apply")

            (data_dir / "review_queue.json").write_text(json.dumps({"items": []}), encoding="utf-8")
            app.review_queue = app.review_queue.__class__(data_dir / "review_queue.json")
            app.proposal_interpreter = _StubInterpreter(confidence=0.70)

            cluster = CandidateCluster(
                cluster_id="cluster_new",
                parent_category="documents",
                file_count=3,
                dominant_extensions=[".pdf"],
                top_tokens=["invoice"],
                pattern_signals={"dated_or_numbered": 1.0},
                example_files=[str(file_path)],
                candidate_files=[str(file_path)],
                heuristic_score=0.9,
                cluster_type="token_group",
            )

            app._refresh_review_queue([cluster])
            item = app.list_review_items()[0]

            self.assertEqual(item.base_confidence, 0.70)
            self.assertGreater(item.final_confidence, item.base_confidence)
            self.assertTrue(item.preference_reasons)


if __name__ == "__main__":
    unittest.main()
