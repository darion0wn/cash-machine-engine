"""Safely rebuild deterministic rankings without changing AI verdicts.

The command is read-only by default. Pass ``--apply`` to persist changes.
Before writing, it saves the current ranking fields to a JSON backup. All
ranking updates are then committed in a single database transaction.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from database.analysis_repository import AnalysisRepository
from services.ranking_engine import RankingEngine

DEFAULT_BACKUP_DIR = Path("backups") / "ranking-rebuild"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Recalculate ranking_score and portfolio_status. The default is "
            "a read-only dry run; pass --apply to write changes."
        )
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Persist ranking changes (creates a JSON backup first).",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Show proposed changes without writing (default).",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=DEFAULT_BACKUP_DIR,
        help=f"Directory for the pre-update backup (default: {DEFAULT_BACKUP_DIR}).",
    )
    return parser


def _backup_path(backup_dir: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return backup_dir / f"ranking-rebuild-{timestamp}.json"


def _write_backup(backup_dir: Path, original_records: list[dict]) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    path = _backup_path(backup_dir)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "Restore ranking_score and portfolio_status before rebuild",
        "records": original_records,
    }
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return path


def _status_label(value) -> str:
    return str(value or "(null)").upper()


def _summarize(analyses: list, ranking_engine: RankingEngine) -> tuple[list, Counter, Counter, int, list[dict], list[dict]]:
    updates = []
    transitions = Counter()
    score_changes = Counter()
    unchanged = 0
    original_records = []
    proposed_records = []

    for analysis in analyses:
        old_score = analysis.ranking_score
        old_status = analysis.portfolio_status
        original_records.append({
            "analysis_id": analysis.id,
            "ranking_score": old_score,
            "portfolio_status": old_status,
        })
        ranking_engine.calculate(analysis)
        new_score = analysis.ranking_score
        new_status = analysis.portfolio_status
        proposed_records.append({
            "analysis_id": analysis.id,
            "old_ranking_score": old_score,
            "new_ranking_score": new_score,
            "old_portfolio_status": old_status,
            "new_portfolio_status": new_status,
        })

        if old_score != new_score or old_status != new_status:
            updates.append((new_score, new_status, analysis.id))
            transitions[f"{_status_label(old_status)} -> {_status_label(new_status)}"] += 1
            if old_score != new_score:
                score_changes["score_changed"] += 1
        else:
            unchanged += 1

    return updates, transitions, score_changes, unchanged, original_records, proposed_records


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    apply_changes = bool(args.apply)
    repository = AnalysisRepository()

    try:
        analyses = repository.find_all()
        ranking_engine = RankingEngine()
        (
            updates,
            transitions,
            score_changes,
            unchanged,
            original_records,
            proposed_records,
        ) = _summarize(analyses, ranking_engine)

        print("=" * 80)
        print(" RANKING REBUILD — " + ("APPLY" if apply_changes else "DRY RUN"))
        print("=" * 80)
        print(f"Analyses inspected : {len(analyses)}")
        print(f"Records to update  : {len(updates)}")
        print(f"Records unchanged  : {unchanged}")
        print(f"Scores changed     : {score_changes['score_changed']}")
        print("Status transitions :")
        if transitions:
            for transition, count in sorted(transitions.items()):
                print(f"  {transition:<22} {count:>5}")
        else:
            print("  None")

        if updates:
            proposed_by_id = {record["analysis_id"]: record for record in proposed_records}
            print("\nSample changes (up to 20):")
            for _, _, analysis_id in updates[:20]:
                record = proposed_by_id[analysis_id]
                print(
                    f"  analysis {analysis_id}: "
                    f"{record['old_ranking_score']} ({record['old_portfolio_status']}) "
                    f"-> {record['new_ranking_score']} ({record['new_portfolio_status']})"
                )

        if not apply_changes:
            print("\nDry run only: no database rows were modified.")
            print("Run with --apply to save changes after reviewing this summary.")
            return 0

        backup_path = _write_backup(args.backup_dir, original_records)
        print(f"\nPre-update ranking backup: {backup_path}")

        try:
            repository.update_rankings_batch(updates)
            repository.db.conn.commit()
        except Exception:
            repository.db.conn.rollback()
            raise

        print(f"Committed ranking updates: {len(updates)}")
        print("AI build_verdict and founder decisions were not modified.")
        return 0
    except Exception as exc:
        print(f"Ranking rebuild failed: {exc}", file=sys.stderr)
        return 1
    finally:
        repository.close()


if __name__ == "__main__":
    raise SystemExit(main())
