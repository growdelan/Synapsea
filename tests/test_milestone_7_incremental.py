from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.config import AppConfig
from synapsea.pipeline import SynapseaApp
from synapsea.storage import DecisionLogRepository


class Milestone7IncrementalTest(unittest.TestCase):
    def test_run_once_processes_only_delta_and_handles_deleted_files(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_dir = root / "downloads"
            data_dir = root / "data"
            source_dir.mkdir()

            image_path = source_dir / "Screenshot-2026-03-24.png"
            doc_path = source_dir / "invoice_v1.pdf"
            image_path.write_text("stub", encoding="utf-8")
            doc_path.write_text("stub", encoding="utf-8")

            app = SynapseaApp.from_config(
                AppConfig(source_dir=source_dir, data_dir=data_dir, enable_ai_review=False)
            )
            first_processed = app.run_once()

            doc_path.write_text("updated", encoding="utf-8")
            archive_path = source_dir / "package_v1.zip"
            archive_path.write_text("stub", encoding="utf-8")
            image_path.unlink()

            second_processed = app.run_once()
            decisions = DecisionLogRepository(data_dir / "classification_log.db").list_all()
            paths = {item.file_path for item in decisions}

            self.assertEqual(first_processed, 2)
            self.assertEqual(second_processed, 2)
            self.assertNotIn(str(image_path), paths)
            self.assertIn(str(doc_path), paths)
            self.assertIn(str(archive_path), paths)


if __name__ == "__main__":
    unittest.main()
