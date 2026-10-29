import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import rebuild_rankings


def sample_analysis():
    return SimpleNamespace(
        id=7,
        ranking_score=20,
        portfolio_status="SKIP",
        cash_machine_score=80,
        confidence=10,
        ai_leverage_score=10,
        distribution_score=10,
        problem_score=10,
        business_score=10,
        build_verdict="WATCH",
    )


class RebuildRankingsTests(unittest.TestCase):
    def make_repository(self, item):
        repo = MagicMock()
        repo.find_all.return_value = [item]
        repo.db.conn = MagicMock()
        return repo

    def test_default_mode_is_read_only(self):
        item = sample_analysis()
        repo = self.make_repository(item)
        with patch.object(rebuild_rankings, "AnalysisRepository", return_value=repo):
            with tempfile.TemporaryDirectory() as temp_dir:
                result = rebuild_rankings.main(["--backup-dir", temp_dir])
                self.assertEqual(result, 0)
                repo.update_rankings_batch.assert_not_called()
                repo.db.conn.commit.assert_not_called()
                self.assertEqual(list(Path(temp_dir).iterdir()), [])

    def test_apply_writes_backup_then_commits_batch(self):
        item = sample_analysis()
        repo = self.make_repository(item)
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(rebuild_rankings, "AnalysisRepository", return_value=repo):
                result = rebuild_rankings.main(["--apply", "--backup-dir", temp_dir])
            self.assertEqual(result, 0)
            repo.update_rankings_batch.assert_called_once()
            repo.db.conn.commit.assert_called_once()
            backup_files = list(Path(temp_dir).glob("*.json"))
            self.assertEqual(len(backup_files), 1)
            payload = json.loads(backup_files[0].read_text(encoding="utf-8"))
            self.assertEqual(payload["records"][0]["ranking_score"], 20)
            self.assertEqual(payload["records"][0]["portfolio_status"], "SKIP")
            self.assertEqual(item.build_verdict, "WATCH")

    def test_apply_rolls_back_if_batch_update_fails(self):
        item = sample_analysis()
        repo = self.make_repository(item)
        repo.update_rankings_batch.side_effect = RuntimeError("simulated write failure")
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(rebuild_rankings, "AnalysisRepository", return_value=repo), \
                 patch("rebuild_rankings.sys.stderr"):
                result = rebuild_rankings.main(["--apply", "--backup-dir", temp_dir])
            self.assertEqual(result, 1)
            repo.db.conn.rollback.assert_called_once()
            repo.db.conn.commit.assert_not_called()
            self.assertEqual(len(list(Path(temp_dir).glob("*.json"))), 1)

    def test_backup_contains_only_fields_rebuild_can_change(self):
        item = sample_analysis()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = rebuild_rankings._write_backup(Path(temp_dir), [{
                "analysis_id": item.id,
                "ranking_score": item.ranking_score,
                "portfolio_status": item.portfolio_status,
            }])
            payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(set(payload["records"][0]), {
            "analysis_id", "ranking_score", "portfolio_status"
        })


if __name__ == "__main__":
    unittest.main()
