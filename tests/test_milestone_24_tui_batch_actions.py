from __future__ import annotations

import asyncio
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from textual.widgets import SelectionList

from synapsea.config import AppConfig
from synapsea.tui.app import SynapseaTuiApp
from synapsea.tui.controllers.app_controller import AppController


def _prepare_batch_fixture(source_dir: Path, data_dir: Path) -> None:
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


class Milestone24TuiBatchActionsTest(unittest.TestCase):
    def test_controller_apply_selected_aggregates_results(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            source_dir = Path(tmp_dir) / "source"
            data_dir = Path(tmp_dir) / "data"
            _prepare_batch_fixture(source_dir, data_dir)
            config = AppConfig.from_args(source=source_dir, data_dir=data_dir, enable_ai_review=False)
            controller = AppController.from_config(config)

            report = controller.apply_selected(["rev_001", "rev_002"])

            self.assertEqual(report.succeeded_count, 2)
            self.assertEqual(report.failed_count, 0)
            self.assertEqual(report.moved, 2)

    def test_controller_reject_selected_continues_after_error(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            source_dir = Path(tmp_dir) / "source"
            data_dir = Path(tmp_dir) / "data"
            _prepare_batch_fixture(source_dir, data_dir)
            config = AppConfig.from_args(source=source_dir, data_dir=data_dir, enable_ai_review=False)
            controller = AppController.from_config(config)

            report = controller.reject_selected(["rev_001", "missing", "rev_002"])

            self.assertEqual(report.succeeded_count, 2)
            self.assertEqual(report.failed_count, 1)
            self.assertIn("missing", report.failures[0])

    def test_tui_batch_apply_shows_result_and_clears_pending_items(self) -> None:
        async def runner() -> None:
            with TemporaryDirectory() as tmp_dir:
                source_dir = Path(tmp_dir) / "source"
                data_dir = Path(tmp_dir) / "data"
                _prepare_batch_fixture(source_dir, data_dir)
                config = AppConfig.from_args(source=source_dir, data_dir=data_dir, enable_ai_review=False)
                app = SynapseaTuiApp.from_config(config)

                async with app.run_test() as pilot:
                    await pilot.press("w", "x", "a", "enter", "enter")
                    selection_list = app.screen.query_one(SelectionList)
                    self.assertEqual(len(selection_list.options), 0)
                    await pilot.press("q")

        asyncio.run(runner())

    def test_tui_batch_reject_shows_result_and_clears_pending_items(self) -> None:
        async def runner() -> None:
            with TemporaryDirectory() as tmp_dir:
                source_dir = Path(tmp_dir) / "source"
                data_dir = Path(tmp_dir) / "data"
                _prepare_batch_fixture(source_dir, data_dir)
                config = AppConfig.from_args(source=source_dir, data_dir=data_dir, enable_ai_review=False)
                app = SynapseaTuiApp.from_config(config)

                async with app.run_test() as pilot:
                    await pilot.press("w", "x", "r", "enter", "enter")
                    selection_list = app.screen.query_one(SelectionList)
                    self.assertEqual(len(selection_list.options), 0)
                    await pilot.press("q")

        asyncio.run(runner())
