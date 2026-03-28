from __future__ import annotations

import io
import unittest

from synapsea.cli import _print_review_items
from synapsea.models import ReviewItem


class Milestone10ReviewCliTest(unittest.TestCase):
    def test_print_review_items_basic_mode_shows_context_columns(self) -> None:
        item = ReviewItem(
            item_id="rev_001",
            item_type="create_category",
            status="pending",
            confidence=0.91,
            parent_category="documents",
            proposed_category="guides",
            target_path="documents/guides",
            candidate_files=["/tmp/a.pdf", "/tmp/b.pdf"],
            reason="To jest dlugie uzasadnienie, ktore powinno byc przyciete w trybie podstawowym.",
            cluster_id="cluster_001",
        )
        out = io.StringIO()

        _print_review_items([item], verbose=False, out=out)
        line = out.getvalue().strip()
        parts = line.split("\t")

        self.assertEqual(parts[0], "rev_001")
        self.assertEqual(parts[1], "pending")
        self.assertEqual(parts[5], "documents/guides")
        self.assertEqual(parts[6], "2")
        self.assertEqual(len(parts), 7)

    def test_print_review_items_verbose_mode_keeps_minimal_format(self) -> None:
        item = ReviewItem(
            item_id="rev_002",
            item_type="create_category",
            status="pending",
            confidence=0.95,
            parent_category="images",
            proposed_category="winter",
            target_path="images/winter",
            candidate_files=["/tmp/a.png", "/tmp/b.png", "/tmp/c.png", "/tmp/d.png"],
            reason="Pelne uzasadnienie.",
            cluster_id="cluster_002",
        )
        out = io.StringIO()

        _print_review_items([item], verbose=True, out=out)
        line = out.getvalue().strip()
        parts = line.split("\t")

        self.assertEqual(parts[0], "rev_002")
        self.assertEqual(parts[6], "4")
        self.assertEqual(len(parts), 7)


if __name__ == "__main__":
    unittest.main()
