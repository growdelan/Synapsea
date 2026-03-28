from __future__ import annotations

import asyncio
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.config import AppConfig
from synapsea.tui.app import SynapseaTuiApp
from synapsea.tui.controllers.app_controller import AppController


class Milestone22TuiDashboardRunTest(unittest.TestCase):
    def test_controller_run_now_updates_status_and_last_run(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            source_dir = Path(tmp_dir) / "source"
            data_dir = Path(tmp_dir) / "data"
            source_dir.mkdir()
            data_dir.mkdir()
            (source_dir / "invoice.pdf").write_text("demo", encoding="utf-8")
            config = AppConfig.from_args(source=source_dir, data_dir=data_dir, enable_ai_review=False)
            controller = AppController.from_config(config)

            snapshot = controller.run_now()

            self.assertEqual(snapshot.last_operation_status, "success")
            self.assertIn("Processed 1 file(s).", snapshot.last_operation_message)
            self.assertNotEqual(snapshot.last_run_at, "brak danych")

    def test_tui_run_now_refreshes_dashboard_summary(self) -> None:
        async def runner() -> None:
            with TemporaryDirectory() as tmp_dir:
                source_dir = Path(tmp_dir) / "source"
                data_dir = Path(tmp_dir) / "data"
                source_dir.mkdir()
                data_dir.mkdir()
                (source_dir / "invoice.pdf").write_text("demo", encoding="utf-8")
                config = AppConfig.from_args(source=source_dir, data_dir=data_dir, enable_ai_review=False)
                app = SynapseaTuiApp.from_config(config)

                async with app.run_test() as pilot:
                    await pilot.press("r")
                    summary_widget = app.screen.query_one("#dashboard-summary")
                    self.assertIn("Processed 1 file(s).", str(summary_widget.render()))
                    await pilot.press("q")

        asyncio.run(runner())
