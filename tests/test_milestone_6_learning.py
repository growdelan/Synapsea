from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.config import AppConfig
from synapsea.evolution_engine import EvolutionEngine
from synapsea.models import LearningSignal, TaxonomyNode
from synapsea.pipeline import SynapseaApp


class Milestone6LearningTest(unittest.TestCase):
    def test_run_once_records_manual_rename_signal(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_dir = root / "downloads"
            data_dir = root / "data"
            source_dir.mkdir()
            original_path = source_dir / "draft_invoice.pdf"
            original_path.write_text("stub", encoding="utf-8")

            app = SynapseaApp.from_config(AppConfig(source_dir=source_dir, data_dir=data_dir, enable_ai_review=False))
            app.run_once()

            renamed_path = source_dir / "final_invoice.pdf"
            original_path.rename(renamed_path)
            app.run_once()

            signals = json.loads((data_dir / "learning_signals.json").read_text(encoding="utf-8"))
            self.assertTrue(any(item["signal_type"] == "manual_rename" for item in signals["signals"]))

    def test_evolution_engine_builds_follow_up_review_items(self) -> None:
        signals = [
            LearningSignal(
                signal_id="sig_001",
                signal_type="manual_rename",
                category="documents",
                file_path="/tmp/final_invoice.pdf",
                details={"suggested_category": "invoice"},
            ),
            LearningSignal(
                signal_id="sig_001b",
                signal_type="manual_rename",
                category="documents",
                file_path="/tmp/final_invoice_2.pdf",
                details={"suggested_category": "invoice"},
            ),
            LearningSignal(
                signal_id="sig_002",
                signal_type="review_rejected",
                category="documents",
                file_path="/tmp/documents/invoices",
                details={"proposed_category": "invoices"},
            ),
            LearningSignal(
                signal_id="sig_003",
                signal_type="review_rejected",
                category="documents",
                file_path="/tmp/documents/invoices_2",
                details={"proposed_category": "invoices"},
            ),
        ]
        taxonomy = {"screenshots": TaxonomyNode(children=[], status="proposed")}

        proposals = EvolutionEngine().build_proposals(signals, taxonomy)

        proposal_types = {proposal.item_type for proposal in proposals}
        self.assertIn("create_subcategory", proposal_types)
        self.assertIn("merge_category", proposal_types)
        self.assertIn("dead_category", proposal_types)

    def test_evolution_engine_filters_singletons_and_low_quality_tokens(self) -> None:
        signals = [
            LearningSignal(
                signal_id="sig_010",
                signal_type="manual_rename",
                category="documents",
                file_path="/tmp/a",
                details={"suggested_category": "2501"},
            ),
            LearningSignal(
                signal_id="sig_011",
                signal_type="manual_rename",
                category="documents",
                file_path="/tmp/b",
                details={"suggested_category": "cv"},
            ),
            LearningSignal(
                signal_id="sig_012",
                signal_type="manual_rename",
                category="documents",
                file_path="/tmp/c",
                details={"suggested_category": "invoice"},
            ),
        ]

        proposals = EvolutionEngine().build_proposals(signals, {})
        self.assertEqual(proposals, [])
