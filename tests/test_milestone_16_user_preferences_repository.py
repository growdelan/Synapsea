from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.user_preferences import UserPreferencesRepository


class Milestone16UserPreferencesRepositoryTest(unittest.TestCase):
    def test_repository_bootstraps_default_file(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            repo = UserPreferencesRepository(Path(tmp_dir) / "user_preferences.json")
            snapshot = repo.load_snapshot()
            self.assertEqual(snapshot.token_preferences, {})
            self.assertEqual(snapshot.proposal_preferences, {})

    def test_repository_records_accept_and_reject_counts(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            repo = UserPreferencesRepository(Path(tmp_dir) / "user_preferences.json")
            repo.record_token("invoice", "documents/finance", accepted=True)
            repo.record_token("invoice", "documents/finance", accepted=True)
            repo.record_token("invoice", "documents/finance", accepted=False)
            repo.record_proposal_pair("documents::finance", accepted=True)

            snapshot = repo.load_snapshot()
            token_stats = snapshot.token_preferences["invoice"]["documents/finance"]
            pair_stats = snapshot.proposal_preferences["documents::finance"]

            self.assertEqual(token_stats.accept_count, 2)
            self.assertEqual(token_stats.reject_count, 1)
            self.assertGreater(token_stats.score, 0.0)
            self.assertEqual(pair_stats.accept_count, 1)
            self.assertEqual(pair_stats.reject_count, 0)

    def test_repository_handles_multiple_signal_groups(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            repo = UserPreferencesRepository(Path(tmp_dir) / "user_preferences.json")
            repo.record_heuristic("screenshot_like", "images/screenshots", accepted=True)
            repo.record_pattern("dated_or_numbered", "documents/reports", accepted=True)

            snapshot = repo.load_snapshot()
            self.assertIn("screenshot_like", snapshot.heuristic_preferences)
            self.assertIn("dated_or_numbered", snapshot.pattern_preferences)


if __name__ == "__main__":
    unittest.main()
