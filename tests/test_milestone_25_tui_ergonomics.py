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


def _write_ergonomic_fixture(data_dir: Path) -> None:
    (data_dir / "review_queue.json").write_text(
        json.dumps(
            {
                "items": [
                    {
                        "id": "rev_001",
                        "type": "create_category",
                        "status": "pending",
                        "confidence": 0.75,
                        "parent_category": "documents",
                        "proposed_category": "finance",
                        "target_path": "documents/finance",
                        "candidate_files": ["/tmp/a.pdf", "/tmp/b.pdf", "/tmp/c.pdf"],
                        "reason": "Finance invoices",
                        "cluster_id": "cluster_001",
                    },
                    {
                        "id": "rev_002",
                        "type": "create_category",
                        "status": "pending",
                        "confidence": 0.95,
                        "parent_category": "images",
                        "proposed_category": "screenshots",
                        "target_path": "images/screenshots",
                        "candidate_files": ["/tmp/a.png"],
                        "reason": "Screenshot captures",
                        "cluster_id": "cluster_002",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )


class Milestone25TuiErgonomicsTest(unittest.TestCase):
    def test_controller_supports_filter_and_sorting(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            data_dir = Path(tmp_dir)
            _write_ergonomic_fixture(data_dir)
            config = AppConfig.from_args(source=Path("~/Downloads"), data_dir=data_dir, enable_ai_review=False)
            controller = AppController.from_config(config)

            filtered = controller.get_review_items(text_filter="screen", sort_by="confidence")
            by_candidates = controller.get_review_items(sort_by="candidate_count")

            self.assertEqual([item.item_id for item in filtered], ["rev_002"])
            self.assertEqual([item.item_id for item in by_candidates], ["rev_001", "rev_002"])

    def test_controller_run_with_options_updates_active_config(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            source_dir = Path(tmp_dir) / "source"
            data_dir = Path(tmp_dir) / "data"
            source_dir.mkdir()
            data_dir.mkdir()
            (source_dir / "sample.txt").write_text("demo", encoding="utf-8")
            config = AppConfig.from_args(source=Path("~/Downloads"), data_dir=data_dir, enable_ai_review=False)
            controller = AppController.from_config(config)

            snapshot = controller.run_with_options(
                {
                    "source_dir": str(source_dir),
                    "data_dir": str(data_dir),
                    "skip_ai": True,
                    "ollama_model": "llama3.1:8b",
                    "ai_budget": "5",
                    "ai_max_examples": "2",
                }
            )

            self.assertEqual(snapshot.source_dir, str(source_dir))
            self.assertEqual(snapshot.ollama_model, "llama3.1:8b")
            self.assertIn("Processed 1 file(s).", snapshot.last_operation_message)

    def test_tui_filter_and_detail_modal_work(self) -> None:
        async def runner() -> None:
            with TemporaryDirectory() as tmp_dir:
                data_dir = Path(tmp_dir)
                _write_ergonomic_fixture(data_dir)
                config = AppConfig.from_args(source=Path("~/Downloads"), data_dir=data_dir, enable_ai_review=False)
                app = SynapseaTuiApp.from_config(config)

                async with app.run_test() as pilot:
                    await pilot.press("w")
                    app.review_screen.text_filter = "screen"
                    app.apply_review_filter(show_all_statuses=app.review_screen.show_all_statuses)
                    selection_list = app.screen.query_one(SelectionList)
                    self.assertEqual(len(selection_list.options), 1)
                    app.review_screen.action_show_full_detail()
                    await pilot.pause()
                    self.assertIn("Szczegoly", str(app.screen.query_one("#result-title").render()))
                    await pilot.press("enter", "q")

        asyncio.run(runner())
