from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.config import AppConfig
from synapsea.models import ClassificationDecision
from synapsea.pipeline import SynapseaApp


class Milestone17PreferenceLearningApplyRejectTest(unittest.TestCase):
    def test_apply_updates_pair_and_feature_preferences(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_dir = root / "source"
            data_dir = root / "data"
            source_dir.mkdir(parents=True, exist_ok=True)
            data_dir.mkdir(parents=True, exist_ok=True)

            file_path = source_dir / "invoice_001.pdf"
            file_path.write_text("x", encoding="utf-8")

            (data_dir / "review_queue.json").write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "id": "rev_001",
                                "type": "create_category",
                                "status": "pending",
                                "confidence": 0.9,
                                "parent_category": "documents",
                                "proposed_category": "finance",
                                "target_path": "documents/finance",
                                "candidate_files": [str(file_path)],
                                "reason": "test",
                                "cluster_id": "cluster_001",
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
                    reason="test",
                    confidence=0.9,
                    extension=".pdf",
                    tokens=["invoice", "march"],
                    heuristic_classes=["document_like"],
                    pattern_signals={"dated_or_numbered": 1.0},
                )
            )

            app.apply_review_item("rev_001")

            preferences = json.loads((data_dir / "user_preferences.json").read_text(encoding="utf-8"))
            pair = preferences["proposal_preferences"]["documents::finance"]
            token = preferences["token_preferences"]["invoice"]["documents/finance"]
            heuristic = preferences["heuristic_preferences"]["document_like"]["documents/finance"]

            self.assertEqual(pair["accept_count"], 1)
            self.assertEqual(token["accept_count"], 1)
            self.assertEqual(heuristic["accept_count"], 1)

    def test_reject_updates_negative_pair_signal(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_dir = root / "source"
            data_dir = root / "data"
            source_dir.mkdir(parents=True, exist_ok=True)
            data_dir.mkdir(parents=True, exist_ok=True)

            (data_dir / "review_queue.json").write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "id": "rev_002",
                                "type": "create_category",
                                "status": "pending",
                                "confidence": 0.85,
                                "parent_category": "documents",
                                "proposed_category": "receipts",
                                "target_path": "documents/receipts",
                                "candidate_files": [],
                                "reason": "test",
                                "cluster_id": "cluster_002",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            app = SynapseaApp.from_config(
                AppConfig(source_dir=source_dir, data_dir=data_dir, enable_ai_review=False)
            )
            app.reject_review_item("rev_002")

            preferences = json.loads((data_dir / "user_preferences.json").read_text(encoding="utf-8"))
            pair = preferences["proposal_preferences"]["documents::receipts"]
            self.assertEqual(pair["accept_count"], 0)
            self.assertEqual(pair["reject_count"], 1)


if __name__ == "__main__":
    unittest.main()
