from __future__ import annotations

import subprocess
import sys
import threading
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

from config.settings import SCHEDULER_TIMEZONE
from database.database import Database


class RefreshService:
    """Runs the existing crawler/pipeline workflow in one background job."""

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

        return datetime.now(timezone).replace(tzinfo=None).isoformat(
            timespec="seconds"
        )

    @staticmethod
    def _create_run(started_at: str, trigger: str) -> int:
        db = Database()

        try:
            cursor = db.conn.cursor()
            cursor.execute(
                """
                INSERT INTO refresh_runs (
                    started_at,
                    status,
                    message,
                    trigger
                )
                VALUES (?, 'running', ?, ?)
                """,
                (
                    started_at,
                    "Crawler and analysis worker are running.",
                    trigger,
                ),
            )
            db.conn.commit()
            return int(cursor.lastrowid)
        finally:
            db.conn.close()

    @staticmethod
    def _finish_run(
        run_id: int | None,
        finished_at: str,
        status: str,
        return_code: int | None,
        message: str,
    ) -> None:
        if run_id is None:
            return

        db = Database()

        try:
            db.conn.execute(
                """
                UPDATE refresh_runs
                SET
                    finished_at = ?,
                    status = ?,
                    return_code = ?,
                    message = ?
                WHERE id = ?
                """,
                (
                    finished_at,
                    status,
                    return_code,
                    message,
                    run_id,
                ),
            )
            db.conn.commit()
        finally:
            db.conn.close()

    def get_status(self) -> dict:
        with self._lock:
            return dict(self._status)

    def start(self, trigger: str = "manual") -> bool:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return False

            started_at = self._now()
            run_id = self._create_run(started_at, trigger)

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
                args=(run_id, trigger),
                name="cash-machine-refresh",
                daemon=True,
            )
            self._thread.start()

            return True

    def _run(self, run_id: int | None, trigger: str) -> None:
        root_dir = Path(__file__).resolve().parents[2]

        try:
            completed = subprocess.run(
                [sys.executable, "-m", "crawler.main"],
                cwd=str(root_dir),
                check=False,
            )

            finished_at = self._now()
            status = (
                "completed" if completed.returncode == 0 else "failed"
            )
            message = (
                "Refresh completed successfully."
                if completed.returncode == 0
                else "Refresh finished with an error."
            )

            if status == "completed":
                trend_engine = None

                try:
                    from services.trend_engine import TrendEngine

                    trend_engine = TrendEngine()
                    snapshot_count = trend_engine.capture_snapshot()

                    if snapshot_count:
                        message = (
                            "Refresh completed successfully. "
                            f"Captured {snapshot_count} topic trend snapshots."
                        )
                except Exception as snapshot_error:
                    # Do not turn a successful crawler/analysis run into a
                    # failed refresh just because historical trend capture
                    # could not be persisted.
                    message = (
                        "Refresh completed successfully, but trend history "
                        f"could not be captured: {snapshot_error}"
                    )
                finally:
                    if trend_engine is not None:
                        try:
                            trend_engine.repository.db.conn.close()
                        except Exception:
                            pass

            self._finish_run(
                run_id,
                finished_at,
                status,
                completed.returncode,
                message,
            )

            with self._lock:
                self._status["state"] = status
                self._status["finished_at"] = finished_at
                self._status["return_code"] = completed.returncode
                self._status["message"] = message
                self._status["trigger"] = trigger

        except Exception as exc:
            finished_at = self._now()
            message = f"Refresh failed: {exc}"

            self._finish_run(
                run_id,
                finished_at,
                "failed",
                None,
                message,
            )

            with self._lock:
                self._status["state"] = "failed"
                self._status["finished_at"] = finished_at
                self._status["return_code"] = None
                self._status["message"] = message
                self._status["trigger"] = trigger


refresh_service = RefreshService()
