from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.config import AppConfig
from synapsea.feature_extractor import FeatureExtractor
from synapsea.pipeline import SynapseaApp
from synapsea.storage import DecisionLogRepository


class Milestone2ClassificationTest(unittest.TestCase):
    def test_feature_extractor_builds_prd_signals(self) -> None:
        features = FeatureExtractor().extract(Path("/virtual/Screenshot-2026-03-24_v2.png"))

        self.assertEqual(features.extension, "png")
        self.assertIn("screenshot", features.tokens)
        self.assertIn("screenshot", features.keywords)
        self.assertEqual(features.pattern_signals["has_date_ratio"], 1.0)
        self.assertEqual(features.pattern_signals["has_version_ratio"], 1.0)
        self.assertEqual(features.pattern_signals["has_numbering_ratio"], 1.0)
        self.assertIn("screenshot_like", features.heuristic_classes)

    def test_pipeline_records_idempotent_history_with_features(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_dir = root / "downloads"
            data_dir = root / "data"
            source_dir.mkdir()
            (source_dir / "Screenshot-2026-03-24.png").write_text("stub", encoding="utf-8")
            (source_dir / "invoice_v2.pdf").write_text("stub", encoding="utf-8")

            app = SynapseaApp.from_config(
                AppConfig(source_dir=source_dir, data_dir=data_dir, enable_ai_review=False)
            )

            first_processed = app.run_once()
            second_processed = app.run_once()
            decisions = DecisionLogRepository(data_dir / "classification_log.db").list_all()

            self.assertEqual(first_processed, 2)
            self.assertEqual(second_processed, 0)
            self.assertEqual(len(decisions), 2)
            self.assertEqual(decisions[0].category, "images")
            self.assertIn("screenshot_like", decisions[0].heuristic_classes)
            self.assertEqual(decisions[1].category, "documents")
            self.assertEqual(decisions[1].pattern_signals["has_version_ratio"], 1.0)
