from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.config import AppConfig
from synapsea.pipeline import SynapseaApp


def _prepare_fixture(source_dir: Path, data_dir: Path) -> None:
    source_dir.mkdir()
    data_dir.mkdir()
    file_a = source_dir / "invoice-a.pdf"
    file_b = source_dir / "invoice-b.pdf"
    file_a.write_text("a", encoding="utf-8")
    file_b.write_text("b", encoding="utf-8")
    (data_dir / "review_queue.json").write_text(
        json.dumps(
            {
                "items": [
                    {
                        "id": "rev_001",
                        "type": "create_category",
                        "status": "pending",
                        "confidence": 0.91,
                        "parent_category": "documents",
                        "proposed_category": "finance",
                        "target_path": "documents/finance",
                        "candidate_files": [str(file_a)],
                        "reason": "Powtarzalny wzorzec dokumentow.",
                        "cluster_id": "cluster_001",
                    },
                    {
                        "id": "rev_002",
                        "type": "create_category",
                        "status": "pending",
                        "confidence": 0.88,
                        "parent_category": "documents",
                        "proposed_category": "finance",
                        "target_path": "documents/finance",
                        "candidate_files": [str(file_b)],
                        "reason": "Powtarzalny wzorzec dokumentow.",
                        "cluster_id": "cluster_002",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    (data_dir / "taxonomy.json").write_text("{}", encoding="utf-8")


class Milestone22BatchExecutorTest(unittest.TestCase):
    def test_apply_batch_executes_sequentially_and_reports_partial_failure(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            source_dir = Path(tmp_dir) / "source"
            data_dir = Path(tmp_dir) / "data"
            _prepare_fixture(source_dir, data_dir)
            app = SynapseaApp.from_config(
                AppConfig.from_args(source=source_dir, data_dir=data_dir, enable_ai_review=False)
            )

            report = app.apply_review_items(["rev_001", "missing", "rev_002"])

            self.assertEqual(report.requested, 3)
            self.assertEqual(report.succeeded, 2)
            self.assertEqual(report.failed, 1)
            self.assertEqual(report.moved, 2)
            self.assertEqual(report.skipped, 0)
            self.assertEqual(report.errors, 0)
            self.assertTrue(any("missing:" in entry for entry in (report.failures or [])))

    def test_reject_batch_executes_sequentially_and_reports_partial_failure(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            source_dir = Path(tmp_dir) / "source"
            data_dir = Path(tmp_dir) / "data"
            _prepare_fixture(source_dir, data_dir)
            app = SynapseaApp.from_config(
                AppConfig.from_args(source=source_dir, data_dir=data_dir, enable_ai_review=False)
            )

            report = app.reject_review_items(["missing", "rev_001"])

            self.assertEqual(report.requested, 2)
            self.assertEqual(report.succeeded, 1)
            self.assertEqual(report.failed, 1)
            self.assertTrue(any("missing:" in entry for entry in (report.failures or [])))

