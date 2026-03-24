from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.config import AppConfig
from synapsea.pipeline import SynapseaApp


class Milestone3ClustersTest(unittest.TestCase):
    def test_run_once_materializes_candidate_clusters_from_history(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_dir = root / "downloads"
            data_dir = root / "data"
            source_dir.mkdir()
            (source_dir / "Screenshot-2026-03-24.png").write_text("stub", encoding="utf-8")
            (source_dir / "Screenshot-2026-03-25.png").write_text("stub", encoding="utf-8")
            (source_dir / "invoice_v1.pdf").write_text("stub", encoding="utf-8")
            (source_dir / "invoice_v2.pdf").write_text("stub", encoding="utf-8")

            app = SynapseaApp.from_config(AppConfig(source_dir, data_dir, "http://localhost:11434/api/generate", "llama3.2"))

            processed = app.run_once()
            clusters_payload = json.loads((data_dir / "candidate_clusters.json").read_text(encoding="utf-8"))

            self.assertEqual(processed, 4)
            self.assertGreaterEqual(len(clusters_payload), 3)
            cluster_types = {cluster["cluster_type"] for cluster in clusters_payload}
            self.assertIn("token", cluster_types)
            self.assertIn("extension", cluster_types)
            self.assertIn("name_pattern", cluster_types)
