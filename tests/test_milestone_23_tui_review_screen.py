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


def _write_review_fixture(data_dir: Path) -> None:
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
                        "candidate_files": ["/tmp/a.pdf", "/tmp/b.pdf"],
                        "reason": "Powtarzalny wzorzec dokumentow.",
                        "cluster_id": "cluster_001",
                    },
                    {
                        "id": "rev_002",
                        "type": "create_category",
                        "status": "pending",
                        "confidence": 0.88,
                        "parent_category": "images",
                        "proposed_category": "screenshots",
                        "target_path": "images/screenshots",
                        "candidate_files": ["/tmp/c.png"],
                        "reason": "Powtarzalny wzorzec nazw.",
                        "cluster_id": "cluster_002",
                    },
                    {
                        "id": "rev_003",
                        "type": "create_category",
                        "status": "applied",
                        "confidence": 0.70,
                        "parent_category": "archives",
                        "proposed_category": "zips",
                        "target_path": "archives/zips",
                        "candidate_files": ["/tmp/d.zip"],
                        "reason": "Archiwa z podobnym sufiksem.",
                        "cluster_id": "cluster_003",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )


class Milestone23TuiReviewScreenTest(unittest.TestCase):
    def test_controller_filters_pending_by_default(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            data_dir = Path(tmp_dir)
            _write_review_fixture(data_dir)
            config = AppConfig.from_args(source=Path("~/Downloads"), data_dir=data_dir, enable_ai_review=False)
            controller = AppController.from_config(config)

            pending_items = controller.get_review_items(show_all_statuses=False)
            all_items = controller.get_review_items(show_all_statuses=True)

            self.assertEqual(len(pending_items), 2)
            self.assertEqual(len(all_items), 3)

    def test_tui_review_keeps_selection_when_focus_moves(self) -> None:
        async def runner() -> None:
            with TemporaryDirectory() as tmp_dir:
                data_dir = Path(tmp_dir)
                _write_review_fixture(data_dir)
                config = AppConfig.from_args(source=Path("~/Downloads"), data_dir=data_dir, enable_ai_review=False)
                app = SynapseaTuiApp.from_config(config)

                async with app.run_test() as pilot:
                    await pilot.press("w")
                    await pilot.pause()
                    await pilot.press("space", "down")
                    review_screen = app.screen
                    selection_list = review_screen.query_one(SelectionList)
                    self.assertEqual(set(selection_list.selected), {"rev_001"})
                    detail = str(review_screen.query_one("#review-detail").render())
                    self.assertIn("id: rev_002", detail)
                    await pilot.press("q")

        asyncio.run(runner())

    def test_review_filter_all_statuses_and_back_to_pending(self) -> None:
        async def runner() -> None:
            with TemporaryDirectory() as tmp_dir:
                data_dir = Path(tmp_dir)
                _write_review_fixture(data_dir)
                config = AppConfig.from_args(source=Path("~/Downloads"), data_dir=data_dir, enable_ai_review=False)
                app = SynapseaTuiApp.from_config(config)

                async with app.run_test() as pilot:
                    await pilot.press("w")
                    await pilot.pause()
                    await pilot.press("A")
                    selection_list = app.screen.query_one(SelectionList)
                    self.assertEqual(len(selection_list.options), 3)
                    await pilot.press("p")
                    self.assertEqual(len(selection_list.options), 2)
                    await pilot.press("q")

        asyncio.run(runner())

    def test_filter_change_clears_hidden_selections(self) -> None:
        async def runner() -> None:
            with TemporaryDirectory() as tmp_dir:
                data_dir = Path(tmp_dir)
                _write_review_fixture(data_dir)
                config = AppConfig.from_args(source=Path("~/Downloads"), data_dir=data_dir, enable_ai_review=False)
                app = SynapseaTuiApp.from_config(config)

                async with app.run_test() as pilot:
                    await pilot.press("w")
                    await pilot.pause()
                    await pilot.press("A")
                    selection_list = app.screen.query_one(SelectionList)
                    self.assertEqual(len(selection_list.options), 3)
                    await pilot.press("x")
                    selection_list = app.screen.query_one(SelectionList)
                    self.assertEqual(set(selection_list.selected), {"rev_001", "rev_002", "rev_003"})
                    await pilot.press("p")
                    self.assertEqual(set(selection_list.selected), {"rev_001", "rev_002"})
                    await pilot.press("q")

        asyncio.run(runner())
