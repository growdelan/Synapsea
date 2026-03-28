from __future__ import annotations

import unittest
from io import StringIO
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from unittest.mock import patch

from synapsea.bootstrap_segregator import BootstrapSegregator
from synapsea.cli import main
from synapsea.config import AppConfig
from synapsea.pipeline import SynapseaApp
from synapsea.watcher import WatchService


class Milestone24BootstrapReportingTest(unittest.TestCase):
    def test_run_prints_bootstrap_report(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_dir = root / "source"
            data_dir = root / "data"
            source_dir.mkdir()
            (source_dir / "invoice.pdf").write_text("stub", encoding="utf-8")

            out = StringIO()
            with patch("sys.stdout", out):
                exit_code = main(
                    [
                        "run",
                        "--skip-ai",
                        "--source",
                        str(source_dir),
                        "--data-dir",
                        str(data_dir),
                    ]
                )

            self.assertEqual(exit_code, 0)
            rendered = out.getvalue()
            self.assertIn("Bootstrap segregation requested=1 moved=1 skipped=0 errors=0", rendered)
            self.assertIn("Processed 1 file(s).", rendered)

    def test_segregator_skips_collision_without_overwrite(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            source_dir = Path(tmp_dir)
            incoming = source_dir / "invoice.pdf"
            target_dir = source_dir / "Dokumenty"
            target_path = target_dir / incoming.name
            target_dir.mkdir(parents=True, exist_ok=True)
            incoming.write_text("new", encoding="utf-8")
            target_path.write_text("existing", encoding="utf-8")

            report = BootstrapSegregator(source_dir).segregate_root_files()

            self.assertEqual(report.requested, 1)
            self.assertEqual(report.moved, 0)
            self.assertEqual(report.skipped, 1)
            self.assertEqual(report.errors, 0)
            self.assertEqual(target_path.read_text(encoding="utf-8"), "existing")
            self.assertEqual(incoming.read_text(encoding="utf-8"), "new")

    def test_segregator_reports_move_errors_and_continues(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            source_dir = Path(tmp_dir)
            failing = source_dir / "broken.pdf"
            succeeding = source_dir / "music.mp3"
            failing.write_text("stub", encoding="utf-8")
            succeeding.write_text("stub", encoding="utf-8")
            real_move = shutil.move

            def _move_with_failure(src: str, dst: str) -> str:
                if src.endswith("broken.pdf"):
                    raise OSError("boom")
                return real_move(src, dst)

            with patch("synapsea.bootstrap_segregator.shutil.move", side_effect=_move_with_failure):
                report = BootstrapSegregator(source_dir).segregate_root_files()

            self.assertEqual(report.requested, 2)
            self.assertEqual(report.moved, 1)
            self.assertEqual(report.skipped, 0)
            self.assertEqual(report.errors, 1)
            self.assertTrue(failing.exists())
            self.assertTrue((source_dir / "Audio" / "music.mp3").exists())

    def test_watch_emits_bootstrap_report_on_first_poll(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_dir = root / "source"
            data_dir = root / "data"
            source_dir.mkdir()
            (source_dir / "sample.zip").write_text("stub", encoding="utf-8")
            app = SynapseaApp.from_config(
                AppConfig.from_args(source=source_dir, data_dir=data_dir, enable_ai_review=False)
            )
            captured: list[tuple[int, int, int, int]] = []
            watcher = WatchService(
                app=app,
                source_dir=source_dir,
                poll_interval_seconds=0.2,
                on_bootstrap_report=lambda report: captured.append(
                    (report.requested, report.moved, report.skipped, report.errors)
                ),
            )

            self.assertEqual(watcher.poll_once(), 0)
            self.assertEqual(captured, [(1, 1, 0, 0)])


if __name__ == "__main__":
    unittest.main()
