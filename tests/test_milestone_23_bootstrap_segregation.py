from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.config import AppConfig
from synapsea.pipeline import SynapseaApp
from synapsea.storage import DecisionLogRepository
from synapsea.watcher import WatchService


class Milestone23BootstrapSegregationTest(unittest.TestCase):
    def test_bootstrap_moves_only_root_files(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_dir = root / "source"
            data_dir = root / "data"
            nested_dir = source_dir / "nested"
            source_dir.mkdir()
            nested_dir.mkdir()

            root_pdf = source_dir / "invoice.pdf"
            root_png = source_dir / "photo.png"
            nested_mp4 = nested_dir / "movie.mp4"
            root_pdf.write_text("stub", encoding="utf-8")
            root_png.write_text("stub", encoding="utf-8")
            nested_mp4.write_text("stub", encoding="utf-8")

            app = SynapseaApp.from_config(
                AppConfig.from_args(source=source_dir, data_dir=data_dir, enable_ai_review=False)
            )
            report = app.bootstrap_segregate_root_files()

            self.assertEqual(report.requested, 2)
            self.assertEqual(report.moved, 2)
            self.assertEqual(report.skipped, 0)
            self.assertEqual(report.errors, 0)

            self.assertFalse(root_pdf.exists())
            self.assertFalse(root_png.exists())
            self.assertTrue((source_dir / "Dokumenty" / "invoice.pdf").exists())
            self.assertTrue((source_dir / "Zdjęcia" / "photo.png").exists())
            self.assertTrue(nested_mp4.exists())

    def test_run_command_flow_uses_bootstrap_before_processing(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_dir = root / "source"
            data_dir = root / "data"
            source_dir.mkdir()
            (source_dir / "doc.pdf").write_text("stub", encoding="utf-8")

            app = SynapseaApp.from_config(
                AppConfig.from_args(source=source_dir, data_dir=data_dir, enable_ai_review=False)
            )
            app.bootstrap_segregate_root_files()
            processed = app.run_once()

            decisions = DecisionLogRepository(data_dir / "classification_log.db").list_all()
            self.assertEqual(processed, 1)
            self.assertEqual(len(decisions), 1)
            self.assertEqual(Path(decisions[0].file_path).name, "doc.pdf")
            self.assertIn("Dokumenty", decisions[0].file_path)

    def test_watch_first_poll_performs_bootstrap_then_listens(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_dir = root / "source"
            data_dir = root / "data"
            source_dir.mkdir()
            (source_dir / "existing.pdf").write_text("stub", encoding="utf-8")

            app = SynapseaApp.from_config(
                AppConfig.from_args(source=source_dir, data_dir=data_dir, enable_ai_review=False)
            )
            watcher = WatchService(app=app, source_dir=source_dir, poll_interval_seconds=0.2)

            self.assertEqual(watcher.poll_once(), 0)
            self.assertTrue((source_dir / "Dokumenty" / "existing.pdf").exists())
            decisions_after_boot = DecisionLogRepository(data_dir / "classification_log.db").list_all()
            self.assertEqual(len(decisions_after_boot), 0)


if __name__ == "__main__":
    unittest.main()
