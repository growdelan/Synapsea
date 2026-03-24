from __future__ import annotations

import unittest
from pathlib import Path

from synapsea.models import ClassificationDecision
from synapsea.pipeline import SynapseaApp


class FakeDecisionLogRepository:
    def __init__(self) -> None:
        self.decisions: list[ClassificationDecision] = []

    def record(self, decision: ClassificationDecision) -> None:
        self.decisions.append(decision)

    def list_all(self) -> list[ClassificationDecision]:
        return list(self.decisions)


class SmokeTest(unittest.TestCase):
    def test_run_once_records_simple_decisions_without_disk_io(self) -> None:
        decision_log = FakeDecisionLogRepository()
        fake_paths = [Path("/virtual/holiday.png"), Path("/virtual/invoice.pdf")]
        app = SynapseaApp(
            source_dir=Path("/virtual"),
            decision_log=decision_log,
            iter_files=lambda: fake_paths,
        )

        processed = app.run_once()

        self.assertEqual(processed, 2)
        self.assertEqual(
            [decision.category for decision in decision_log.decisions],
            ["images", "documents"],
        )


if __name__ == "__main__":
    unittest.main()
