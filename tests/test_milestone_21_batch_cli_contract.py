from __future__ import annotations

import json
import unittest
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from synapsea.cli import build_parser, main


def _write_review_fixture(data_dir: Path) -> None:
    (data_dir / "review_queue.json").write_text(
        json.dumps(
            {
                "items": [
                    {
                        "id": "rev_001",
                        "type": "create_category",
                        "status": "pending",
                        "confidence": 0.92,
                        "parent_category": "images",
                        "proposed_category": "screenshots",
                        "target_path": "images/screenshots",
                        "candidate_files": ["/tmp/a.png"],
                        "reason": "Powtarzalny wzorzec nazw.",
                        "cluster_id": "cluster_001",
                    },
                    {
                        "id": "rev_002",
                        "type": "create_category",
                        "status": "pending",
                        "confidence": 0.75,
                        "parent_category": "documents",
                        "proposed_category": "invoices",
                        "target_path": "documents/invoices",
                        "candidate_files": ["/tmp/a.pdf"],
                        "reason": "Powtarzalny wzorzec dokumentow.",
                        "cluster_id": "cluster_002",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    (data_dir / "taxonomy.json").write_text("{}", encoding="utf-8")


class Milestone21BatchCliContractTest(unittest.TestCase):
    def test_parser_accepts_multiple_item_ids(self) -> None:
        parser = build_parser()
        apply_args = parser.parse_args(["apply", "rev_001", "rev_002"])
        reject_args = parser.parse_args(["reject", "rev_010", "rev_011", "rev_012"])

        self.assertEqual(apply_args.item_ids, ["rev_001", "rev_002"])
        self.assertEqual(reject_args.item_ids, ["rev_010", "rev_011", "rev_012"])

    def test_apply_batch_summary_and_exit_code_on_partial_failure(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            data_dir = Path(tmp_dir)
            _write_review_fixture(data_dir)
            out = StringIO()
            with patch("sys.stdout", out):
                exit_code = main(["apply", "rev_001", "missing", "rev_002", "--data-dir", str(data_dir)])

            self.assertEqual(exit_code, 1)
            rendered = out.getvalue()
            self.assertIn("Batch apply requested=3 succeeded=2 failed=1", rendered)
            self.assertIn("moved=", rendered)
            self.assertIn("Apply failed missing:", rendered)

    def test_reject_batch_summary_and_exit_code_on_partial_failure(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            data_dir = Path(tmp_dir)
            _write_review_fixture(data_dir)
            out = StringIO()
            with patch("sys.stdout", out):
                exit_code = main(["reject", "missing", "rev_001", "--data-dir", str(data_dir)])

            self.assertEqual(exit_code, 1)
            rendered = out.getvalue()
            self.assertIn("Batch reject requested=2 succeeded=1 failed=1", rendered)
            self.assertIn("Reject failed missing:", rendered)

