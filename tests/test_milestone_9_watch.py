from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.config import AppConfig
from synapsea.pipeline import SynapseaApp
from synapsea.storage import DecisionLogRepository
from synapsea.watcher import WatchService


class FlakyApp:
    def __init__(self) -> None:
        self.calls = 0
        self.input_state_repository = None

    def iter_files(self):
        return []

    def run_once(self) -> int:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("boom")
        return 1

    def _collect_current_paths(self):
        return []

    def _build_input_state(self, paths):
        return {}


class Milestone9WatchTest(unittest.TestCase):
    def test_watch_starts_without_bootstrap_processing_and_handles_new_event(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_dir = root / "downloads"
            data_dir = root / "data"
            source_dir.mkdir()
            (source_dir / "existing.pdf").write_text("stub", encoding="utf-8")

            app = SynapseaApp.from_config(
                AppConfig(source_dir=source_dir, data_dir=data_dir, enable_ai_review=False)
            )
            watcher = WatchService(app=app, source_dir=source_dir, poll_interval_seconds=0.2)

            self.assertEqual(watcher.poll_once(), 0)
            decisions_after_boot = DecisionLogRepository(data_dir / "classification_log.db").list_all()
            self.assertEqual(len(decisions_after_boot), 0)

            (source_dir / "new_invoice.pdf").write_text("stub", encoding="utf-8")
            processed = watcher.poll_once()
            decisions_after_event = DecisionLogRepository(data_dir / "classification_log.db").list_all()

            self.assertEqual(processed, 1)
            self.assertEqual(len(decisions_after_event), 1)
            self.assertEqual(Path(decisions_after_event[0].file_path).name, "new_invoice.pdf")

    def test_watch_poll_once_does_not_crash_on_processing_error(self) -> None:
        app = FlakyApp()
        watcher = WatchService(app=app, source_dir=Path("/virtual"), poll_interval_seconds=0.2)
        self.assertEqual(watcher.poll_once(), 0)
        # Wymuszenie zmiany snapshotu pomiędzy cyklami.
        watcher._snapshot = {"a": (1, 1)}
        self.assertEqual(watcher.poll_once(), 0)


if __name__ == "__main__":
    unittest.main()
