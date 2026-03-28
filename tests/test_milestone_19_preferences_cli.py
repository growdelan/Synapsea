from __future__ import annotations

import json
import unittest
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from synapsea.cli import _print_review_items, build_parser, main
from synapsea.models import ReviewItem


class Milestone19PreferencesCliTest(unittest.TestCase):
    def test_parser_accepts_preferences_command_with_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["preferences", "--data-dir", "./data", "--verbose", "--limit", "20"])
        self.assertEqual(args.command, "preferences")
        self.assertEqual(args.limit, 20)
        self.assertTrue(args.verbose)

    def test_preferences_command_prints_summary(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            data_dir = Path(tmp_dir)
            (data_dir / "user_preferences.json").write_text(
                json.dumps(
                    {
                        "token_preferences": {
                            "invoice": {
                                "documents/finance": {"accept_count": 3, "reject_count": 0, "score": 0.2}
                            }
                        },
                        "heuristic_preferences": {},
                        "pattern_preferences": {},
                        "proposal_preferences": {
                            "documents::finance": {"accept_count": 3, "reject_count": 0, "score": 0.2}
                        },
                        "metadata": {"version": 1},
                    }
                ),
                encoding="utf-8",
            )

            out = StringIO()
            with patch("sys.stdout", out):
                code = main(["preferences", "--data-dir", str(data_dir), "--limit", "5"])

            self.assertEqual(code, 0)
            text = out.getvalue()
            self.assertIn("Top pozytywne pary propozycji:", text)
            self.assertIn("documents::finance", text)
            self.assertIn("invoice -> documents/finance", text)

    def test_review_verbose_keeps_minimal_columns(self) -> None:
        item = ReviewItem(
            item_id="rev_001",
            item_type="create_category",
            status="pending",
            confidence=0.86,
            parent_category="documents",
            proposed_category="finance",
            target_path="documents/finance",
            candidate_files=["/tmp/a.pdf"],
            reason="test",
            cluster_id="cluster_001",
            base_confidence=0.78,
            preference_delta=0.08,
            final_confidence=0.86,
            preference_reasons=["pair:+0.050", "token:+0.030"],
        )
        out = StringIO()

        _print_review_items([item], verbose=True, out=out)
        line = out.getvalue().strip()
        parts = line.split("\t")

        self.assertEqual(parts[0], "rev_001")
        self.assertEqual(parts[1], "pending")
        self.assertEqual(parts[6], "1")
        self.assertEqual(len(parts), 7)


if __name__ == "__main__":
    unittest.main()
