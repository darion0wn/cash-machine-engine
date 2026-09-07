from __future__ import annotations

import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from config.settings import SCHEDULER_TIMEZONE
from database.database import Database


class RefreshService:
    """Run one refresh at a time across all application processes."""

    REFRESH_LOCK_KEY = "cash_machine_engine:refresh"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._status = {
            "state": "idle",
            "started_at": None,
            "finished_at": None,
            "return_code": None,
            "message": "Ready to refresh.",
            "trigger": None,
        }

    @staticmethod
    def _now() -> str:
        try:
            timezone = ZoneInfo(SCHEDULER_TIMEZONE)
        except Exception:
            timezone = ZoneInfo("UTC")
        return datetime.now(timezone).replace(tzinfo=None).isoformat(timespec="seconds")

    @staticmethod
    def _create_run(db: Database, started_at: str, trigger: str) -> int:
        return db.insert_returning_id(
            """
            INSERT INTO refresh_runs (started_at, status, message, trigger)
            VALUES (?, 'running', ?, ?)
            """,
            (
                started_at,
                "Crawler and analysis worker are running.",
                trigger,
            ),
        )

    @staticmethod
    def _finish_run(
        db: Database,
        run_id: int | None,
        finished_at: str,
        status: str,
        return_code: int | None,
        message: str,
    ) -> None:
        if run_id is None:
            return
        db.conn.execute(
            """
            UPDATE refresh_runs
            SET finished_at = ?, status = ?, return_code = ?, message = ?
            WHERE id = ?
            """,
            (finished_at, status, return_code, message, run_id),
        )
        db.conn.commit()

    @staticmethod
    def _capture_trends() -> str | None:
        try:
            from services.trend_engine import TrendEngine

            trend_engine = TrendEngine()
            try:
                snapshot_count = trend_engine.capture_snapshot()
                if snapshot_count:
                    return f"Captured {snapshot_count} topic trend snapshots."
            finally:
                trend_engine.repository.db.conn.close()
        except Exception as snapshot_error:
            return f"Trend history could not be captured: {snapshot_error}"
        return None

    def _acquire_refresh_lock(self) -> Database | None:
        db = Database()
        if not db.try_advisory_lock(self.REFRESH_LOCK_KEY):
            db.conn.close()
            return None
        return db

    def _release_refresh_lock(self, db: Database) -> None:
        try:
            db.release_advisory_lock(self.REFRESH_LOCK_KEY)
        finally:
            db.conn.close()

    def _execute_refresh(self, lock_db: Database, run_id: int, trigger: str, started_at: str) -> int:
        root_dir = Path(__file__).resolve().parents[2]
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "crawler.main"],
                cwd=str(root_dir),
                check=False,
            )
            finished_at = self._now()
            if completed.returncode == 0:
                status = "completed"
                message = "Refresh completed successfully."
                trend_message = self._capture_trends()
                if trend_message and trend_message.startswith("Captured"):
                    message = f"{message} {trend_message}"
                elif trend_message:
                    message = f"{message} {trend_message}"
            else:
                status = "failed"
                message = "Refresh finished with an error."

            self._finish_run(lock_db, run_id, finished_at, status, completed.returncode, message)
            with self._lock:
                self._status = {
                    "state": status,
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "return_code": completed.returncode,
                    "message": message,
                    "run_id": run_id,
                    "trigger": trigger,
                }
            return int(completed.returncode)
        except Exception as exc:
            finished_at = self._now()
            message = f"Refresh failed: {exc}"
            self._finish_run(lock_db, run_id, finished_at, "failed", None, message)
            with self._lock:
                self._status = {
                    "state": "failed",
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "return_code": None,
                    "message": message,
                    "run_id": run_id,
                    "trigger": trigger,
                }
            return 1

    def run_once(self, trigger: str = "manual") -> int:
        """Run synchronously, with a cross-process database lock."""
        with self._lock:
            if self._thread and self._thread.is_alive():
                return 2

        lock_db = self._acquire_refresh_lock()
        if lock_db is None:
            print("[INFO] Refresh skipped because another refresh is already running.")
            return 2

        started_at = self._now()
        try:
            run_id = self._create_run(lock_db, started_at, trigger)
            return self._execute_refresh(lock_db, run_id, trigger, started_at)
        finally:
            self._release_refresh_lock(lock_db)

    def get_status(self) -> dict:
        with self._lock:
            return dict(self._status)

    def start(self, trigger: str = "manual") -> bool:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return False

            lock_db = self._acquire_refresh_lock()
            if lock_db is None:
                return False

            started_at = self._now()
            try:
                run_id = self._create_run(lock_db, started_at, trigger)
            except Exception:
                self._release_refresh_lock(lock_db)
                raise

            self._status = {
                "state": "running",
                "started_at": started_at,
                "finished_at": None,
                "return_code": None,
                "message": "Crawler and analysis worker are running.",
                "run_id": run_id,
                "trigger": trigger,
            }

            self._thread = threading.Thread(
                target=self._run,
                args=(lock_db, run_id, trigger, started_at),
                name="cash-machine-refresh",
                daemon=True,
            )
            self._thread.start()
            return True

    def _run(self, lock_db: Database, run_id: int, trigger: str, started_at: str) -> None:
        try:
            self._execute_refresh(lock_db, run_id, trigger, started_at)
        finally:
            self._release_refresh_lock(lock_db)


refresh_service = RefreshService()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run one Cash Machine Engine refresh.")
    parser.add_argument(
        "--trigger",
        default="scheduled",
        choices={"manual", "scheduled", "cron"},
        help="Refresh trigger label stored in refresh_runs.",
    )
    args = parser.parse_args()
    raise SystemExit(refresh_service.run_once(trigger=args.trigger))
