from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.models import ReviewItem
from synapsea.review_queue import ReviewQueueRepository


class Milestone12ReviewRankingTest(unittest.TestCase):
    def test_list_items_prioritizes_pending_confidence_and_context(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            repo = ReviewQueueRepository(Path(tmp_dir) / "review_queue.json")
            repo.add_item(
                ReviewItem(
                    item_id="rev_010",
                    item_type="create_category",
                    status="applied",
                    confidence=0.99,
                    parent_category="documents",
                    proposed_category="guides",
                    target_path="documents/guides",
                    candidate_files=["/tmp/a.pdf"],
                    reason="done",
                    cluster_id="cluster_010",
                )
            )
            repo.add_item(
                ReviewItem(
                    item_id="rev_020",
                    item_type="create_category",
                    status="pending",
                    confidence=0.82,
                    parent_category="documents",
                    proposed_category="manuals",
                    target_path="documents/manuals",
                    candidate_files=["/tmp/a.pdf", "/tmp/b.pdf", "/tmp/c.pdf"],
                    reason="pending lower confidence",
                    cluster_id="cluster_020",
                )
            )
            repo.add_item(
                ReviewItem(
                    item_id="rev_021",
                    item_type="create_category",
                    status="pending",
                    confidence=0.95,
                    parent_category="documents",
                    proposed_category="papers",
                    target_path="documents/papers",
                    candidate_files=["/tmp/a.pdf"],
                    reason="pending higher confidence",
                    cluster_id="cluster_021",
                )
            )
            repo.add_item(
                ReviewItem(
                    item_id="rev_022",
                    item_type="create_category",
                    status="pending",
                    confidence=0.95,
                    parent_category="documents",
                    proposed_category="reports",
                    target_path="documents/reports",
                    candidate_files=["/tmp/a.pdf", "/tmp/b.pdf"],
                    reason="pending higher context",
                    cluster_id="cluster_022",
                )
            )

            ordered_ids = [item.item_id for item in repo.list_items()]
            self.assertEqual(ordered_ids, ["rev_022", "rev_021", "rev_020", "rev_010"])


if __name__ == "__main__":
    unittest.main()
