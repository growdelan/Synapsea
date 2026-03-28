from __future__ import annotations

import asyncio
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.cli import build_parser
from synapsea.config import AppConfig
from synapsea.tui.app import SynapseaTuiApp
from synapsea.tui.controllers.app_controller import AppController


class Milestone21TuiFoundationTest(unittest.TestCase):
    def test_parser_accepts_tui_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "tui",
                "--source",
                "~/Downloads",
                "--data-dir",
                "./data",
                "--ollama-model",
                "llama3.1:8b",
                "--skip-ai",
            ]
        )

        self.assertEqual(args.command, "tui")
        self.assertEqual(args.ollama_model, "llama3.1:8b")
        self.assertTrue(args.skip_ai)

    def test_controller_builds_dashboard_snapshot_from_backend_state(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            data_dir = Path(tmp_dir)
            (data_dir / "review_queue.json").write_text(
                json.dumps(
                    {
                        "items": [
                            {"id": "rev_001", "type": "create_category", "status": "pending", "confidence": 0.9, "parent_category": "documents", "proposed_category": "finance", "target_path": "documents/finance", "candidate_files": [], "reason": "x", "cluster_id": "cluster_001"},
                            {"id": "rev_002", "type": "create_category", "status": "applied", "confidence": 0.8, "parent_category": "images", "proposed_category": "screenshots", "target_path": "images/screenshots", "candidate_files": [], "reason": "y", "cluster_id": "cluster_002"},
                            {"id": "rev_003", "type": "create_category", "status": "rejected", "confidence": 0.7, "parent_category": "archives", "proposed_category": "zips", "target_path": "archives/zips", "candidate_files": [], "reason": "z", "cluster_id": "cluster_003"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config = AppConfig.from_args(source=Path("~/Downloads"), data_dir=data_dir, enable_ai_review=False)
            controller = AppController.from_config(config)

            snapshot = controller.get_dashboard_snapshot()

            self.assertEqual(snapshot.pending_count, 1)
            self.assertEqual(snapshot.applied_count, 1)
            self.assertEqual(snapshot.rejected_count, 1)
            self.assertEqual(snapshot.last_operation_status, "idle")

    def test_tui_starts_and_shows_dashboard(self) -> None:
        async def runner() -> None:
            with TemporaryDirectory() as tmp_dir:
                data_dir = Path(tmp_dir)
                config = AppConfig.from_args(source=Path("~/Downloads"), data_dir=data_dir, enable_ai_review=False)
                app = SynapseaTuiApp.from_config(config)

                async with app.run_test() as pilot:
                    self.assertIsNotNone(app.screen.query_one("#dashboard-summary"))
                    await pilot.press("q")

        asyncio.run(runner())
