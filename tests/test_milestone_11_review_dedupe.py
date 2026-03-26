from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.models import ReviewItem
from synapsea.review_queue import ReviewQueueRepository


class Milestone11ReviewDedupeTest(unittest.TestCase):
    def test_add_item_deduplicates_semantic_category_variants(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            repo = ReviewQueueRepository(Path(tmp_dir) / "review_queue.json")
            first = ReviewItem(
                item_id="rev_001",
                item_type="create_category",
                status="pending",
                confidence=0.85,
                parent_category="uncategorized",
                proposed_category="Qt Core Libraries",
                target_path="uncategorized/Qt Core Libraries",
                candidate_files=["/tmp/a.dylib"],
                reason="wzor 1",
                cluster_id="cluster_100",
            )
            second = ReviewItem(
                item_id="rev_002",
                item_type="create_category",
                status="pending",
                confidence=0.92,
                parent_category="uncategorized",
                proposed_category="qt-core-libraries",
                target_path="uncategorized/qt-core-libraries",
                candidate_files=["/tmp/b.dylib"],
                reason="wzor 2",
                cluster_id="cluster_101",
            )

            repo.add_item(first)
            repo.add_item(second)
            items = repo.list_items()

            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].confidence, 0.92)
            self.assertIn("/tmp/a.dylib", items[0].candidate_files)
            self.assertIn("/tmp/b.dylib", items[0].candidate_files)

    def test_add_item_still_replaces_by_cluster_id(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            repo = ReviewQueueRepository(Path(tmp_dir) / "review_queue.json")
            first = ReviewItem(
                item_id="rev_001",
                item_type="create_category",
                status="pending",
                confidence=0.7,
                parent_category="documents",
                proposed_category="Guides",
                target_path="documents/Guides",
                candidate_files=["/tmp/g1.pdf"],
                reason="wzor 1",
                cluster_id="cluster_200",
            )
            second = ReviewItem(
                item_id="rev_999",
                item_type="create_category",
                status="pending",
                confidence=0.9,
                parent_category="documents",
                proposed_category="Guides",
                target_path="documents/Guides",
                candidate_files=["/tmp/g2.pdf"],
                reason="wzor 2",
                cluster_id="cluster_200",
            )
            repo.add_item(first)
            repo.add_item(second)
            items = repo.list_items()

            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].confidence, 0.9)
            self.assertEqual(items[0].cluster_id, "cluster_200")


if __name__ == "__main__":
    unittest.main()
