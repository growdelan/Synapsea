from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.config import AppConfig
from synapsea.pipeline import SynapseaApp


class Milestone13ApplyMovesTest(unittest.TestCase):
    def test_apply_moves_files_and_reports_skip_and_errors(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_dir = root / "source"
            data_dir = root / "data"
            source_dir.mkdir(parents=True, exist_ok=True)
            data_dir.mkdir(parents=True, exist_ok=True)

            movable = source_dir / "move_me.png"
            collision = source_dir / "already_exists.png"
            missing = source_dir / "missing.png"
            movable.write_text("move", encoding="utf-8")
            collision.write_text("collision", encoding="utf-8")

            target_dir = source_dir / "images" / "screenshots"
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / collision.name).write_text("target", encoding="utf-8")

            (data_dir / "review_queue.json").write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "id": "rev_001",
                                "type": "create_category",
                                "status": "pending",
                                "confidence": 0.9,
                                "parent_category": "images",
                                "proposed_category": "screenshots",
                                "target_path": "images/screenshots",
                                "candidate_files": [str(movable), str(collision), str(missing)],
                                "reason": "test",
                                "cluster_id": "cluster_001",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (data_dir / "taxonomy.json").write_text("{}", encoding="utf-8")

            app = SynapseaApp.from_config(
                AppConfig(source_dir=source_dir, data_dir=data_dir, enable_ai_review=False)
            )
            applied, report = app.apply_review_item("rev_001")

            self.assertEqual(applied.item_id, "rev_001")
            self.assertEqual(report.moved, 1)
            self.assertEqual(report.skipped, 1)
            self.assertEqual(report.errors, 1)

            self.assertFalse(movable.exists())
            self.assertTrue((target_dir / movable.name).exists())
            self.assertTrue(collision.exists())

            queue = json.loads((data_dir / "review_queue.json").read_text(encoding="utf-8"))
            self.assertEqual(queue["items"][0]["status"], "applied")

            taxonomy = json.loads((data_dir / "taxonomy.json").read_text(encoding="utf-8"))
            self.assertIn("images", taxonomy)
            self.assertIn("screenshots", taxonomy["images"]["children"])
