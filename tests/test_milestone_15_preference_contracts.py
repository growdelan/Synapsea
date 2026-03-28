from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.models import ReviewItem
from synapsea.review_queue import ReviewQueueRepository
from synapsea.user_preferences import PreferenceStats, conservative_evidence_weight


class Milestone15PreferenceContractsTest(unittest.TestCase):
    def test_review_queue_reads_legacy_items_without_preference_fields(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "review_queue.json"
            path.write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "id": "rev_001",
                                "type": "create_category",
                                "status": "pending",
                                "confidence": 0.87,
                                "parent_category": "documents",
                                "proposed_category": "finance",
                                "target_path": "documents/finance",
                                "candidate_files": ["/tmp/a.pdf"],
                                "reason": "legacy",
                                "cluster_id": "cluster_001",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            repo = ReviewQueueRepository(path)
            item = repo.list_items()[0]

            self.assertEqual(item.item_id, "rev_001")
            self.assertEqual(item.final_confidence, None)
            self.assertEqual(item.preference_reasons, [])

    def test_review_item_serialization_keeps_new_fields_optional(self) -> None:
        item = ReviewItem(
            item_id="rev_002",
            item_type="create_category",
            status="pending",
            confidence=0.8,
            parent_category="documents",
            proposed_category="invoices",
            target_path="documents/invoices",
            candidate_files=["/tmp/a.pdf"],
            reason="ok",
            cluster_id="cluster_002",
        )
        payload = item.to_dict()
        self.assertNotIn("base_confidence", payload)
        self.assertNotIn("preference_delta", payload)
        self.assertNotIn("final_confidence", payload)
        self.assertNotIn("preference_reasons", payload)

    def test_conservative_weight_grows_with_repeated_signal(self) -> None:
        self.assertLess(conservative_evidence_weight(1), conservative_evidence_weight(2))
        self.assertLess(conservative_evidence_weight(2), conservative_evidence_weight(3))

    def test_preference_score_is_small_for_single_event(self) -> None:
        stats = PreferenceStats()
        stats.record_accept()
        self.assertLess(abs(stats.score), 0.2)


if __name__ == "__main__":
    unittest.main()
