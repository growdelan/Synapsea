from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.cli import main


class Milestone5CliReviewTest(unittest.TestCase):
    def test_review_apply_and_reject_commands_update_state(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            data_dir = Path(tmp_dir)
            (data_dir / "review_queue.json").write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "id": "rev_001",
                                "type": "create_category",
                                "status": "pending",
                                "confidence": 0.92,
                                "parent_category": "images",
                                "proposed_category": "screenshots",
                                "target_path": "images/screenshots",
                                "candidate_files": ["/tmp/a.png"],
                                "reason": "Powtarzalny wzorzec nazw.",
                                "cluster_id": "cluster_001",
                            },
                            {
                                "id": "rev_002",
                                "type": "create_category",
                                "status": "pending",
                                "confidence": 0.75,
                                "parent_category": "documents",
                                "proposed_category": "invoices",
                                "target_path": "documents/invoices",
                                "candidate_files": ["/tmp/a.pdf"],
                                "reason": "Powtarzalny wzorzec dokumentow.",
                                "cluster_id": "cluster_002",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (data_dir / "taxonomy.json").write_text("{}", encoding="utf-8")

            review_code = main(["review", "--data-dir", str(data_dir)])
            apply_code = main(["apply", "rev_001", "--data-dir", str(data_dir)])
            reject_code = main(["reject", "rev_002", "--data-dir", str(data_dir)])

            self.assertEqual(review_code, 0)
            self.assertEqual(apply_code, 0)
            self.assertEqual(reject_code, 0)

            taxonomy = json.loads((data_dir / "taxonomy.json").read_text(encoding="utf-8"))
            review_queue = json.loads((data_dir / "review_queue.json").read_text(encoding="utf-8"))

            self.assertIn("images", taxonomy)
            self.assertIn("screenshots", taxonomy["images"]["children"])
            status_by_id = {item["id"]: item["status"] for item in review_queue["items"]}
            self.assertEqual(status_by_id["rev_001"], "applied")
            self.assertEqual(status_by_id["rev_002"], "rejected")
