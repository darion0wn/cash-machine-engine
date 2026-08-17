from __future__ import annotations

import threading
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from config.settings import (
    SCHEDULER_CATCH_UP,
    SCHEDULER_CHECK_SECONDS,
    SCHEDULER_ENABLED,
    SCHEDULER_TIME,
    SCHEDULER_TIMEZONE,
)
from core.logger import Logger
from database.database import Database
from web.services.refresh_service import refresh_service


class SchedulerService:
    """Runs one automatic refresh per calendar day while the app is alive."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        self._enabled = bool(SCHEDULER_ENABLED)
        self._hour, self._minute = self._parse_time(SCHEDULER_TIME)
        self._timezone = self._load_timezone(SCHEDULER_TIMEZONE)
        self._check_seconds = max(5, int(SCHEDULER_CHECK_SECONDS))
        self._catch_up = bool(SCHEDULER_CATCH_UP)

        self._status = {
            "enabled": self._enabled,
            "state": "stopped",
            "schedule": self.schedule_label,
            "timezone": getattr(self._timezone, "key", "UTC"),
            "last_scheduled_run": None,
            "next_run": self._next_run().isoformat(timespec="seconds"),
            "message": (
                "Scheduler is disabled."
                if not self._enabled
                else "Scheduler is ready."
            ),
        }

    @staticmethod
    def _parse_time(value: str) -> tuple[int, int]:
        try:
            hour_text, minute_text = value.strip().split(":", 1)
            hour = int(hour_text)
            minute = int(minute_text)

            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError

            return hour, minute

        except (AttributeError, ValueError):
            Logger.warning(
                f"Invalid scheduler time '{value}'. Falling back to 07:00."
            )
            return 7, 0

    @staticmethod
    def _load_timezone(name: str) -> ZoneInfo:
        try:
            return ZoneInfo(name)
        except Exception:
            Logger.warning(
                f"Invalid scheduler timezone '{name}'. Falling back to UTC."
            )
            return ZoneInfo("UTC")

    @property
    def schedule_label(self) -> str:
        return f"{self._hour:02d}:{self._minute:02d} daily"

    def _now(self) -> datetime:
        return datetime.now(self._timezone)

    def _scheduled_datetime(self, target_date: date) -> datetime:
        return datetime(
            target_date.year,
            target_date.month,
            target_date.day,
            self._hour,
            self._minute,
            tzinfo=self._timezone,
        )

    def _next_run(self) -> datetime:
        now = self._now()
        candidate = self._scheduled_datetime(now.date())

        if candidate <= now:
            candidate = self._scheduled_datetime(
                now.date() + timedelta(days=1)
            )

        return candidate

    @staticmethod
    def _get_successful_or_running_refresh_today(target_date: date) -> dict | None:
        db = Database()

        try:
            row = db.conn.execute(
                """
                SELECT started_at, finished_at, status, trigger
                FROM refresh_runs
                WHERE substr(started_at, 1, 10) = ?
                  AND status IN ('running', 'completed')
                ORDER BY id DESC
                LIMIT 1
                """,
                (target_date.isoformat(),),
            ).fetchone()

            if row is None:
                return None

            return {
                "started_at": row[0],
                "finished_at": row[1],
                "status": row[2],
                "trigger": row[3],
            }

        finally:
            db.conn.close()

    @staticmethod
    def _get_scheduled_run_today(target_date: date) -> dict | None:
        db = Database()

        try:
            row = db.conn.execute(
                """
                SELECT
                    id,
                    started_at,
                    finished_at,
                    status,
                    return_code,
                    message,
                    trigger
                FROM refresh_runs
                WHERE substr(started_at, 1, 10) = ?
                  AND trigger = 'scheduled'
                ORDER BY id DESC
                LIMIT 1
                """,
                (target_date.isoformat(),),
            ).fetchone()

            if row is None:
                return None

            return {
                "id": row[0],
                "started_at": row[1],
                "finished_at": row[2],
                "status": row[3],
                "return_code": row[4],
                "message": row[5],
                "trigger": row[6],
            }

        finally:
            db.conn.close()

    def _should_run_today(self, now: datetime) -> bool:
        scheduled_at = self._scheduled_datetime(now.date())

        if now < scheduled_at:
            return False

        # Only one scheduled attempt per calendar day. This prevents a failed
        # scheduled refresh from being retried on every polling interval.
        if self._get_scheduled_run_today(now.date()) is not None:
            return False

        if self._get_successful_or_running_refresh_today(now.date()) is not None:
            return False

        if self._catch_up:
            return True

        return now <= scheduled_at + timedelta(minutes=1)

    @staticmethod
    def _get_last_refresh() -> dict | None:
        db = Database()

        try:
            row = db.conn.execute(
                """
                SELECT started_at, status, trigger
                FROM refresh_runs
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()

            if row is None:
                return None

            return {
                "started_at": row[0],
                "status": row[1],
                "trigger": row[2],
            }

        finally:
            db.conn.close()

    def get_status(self) -> dict:
        now = self._now()
        scheduled_today = self._get_scheduled_run_today(now.date())

        with self._lock:
            status = dict(self._status)

        status["next_run"] = self._next_run().isoformat(timespec="seconds")
        status["last_scheduled_run"] = (
            scheduled_today.get("started_at")
            if scheduled_today
            else None
        )

        last_refresh = self._get_last_refresh()
        status["last_refresh"] = (
            last_refresh.get("started_at") if last_refresh else None
        )
        status["last_refresh_trigger"] = (
            last_refresh.get("trigger") if last_refresh else None
        )

        return status

    def start(self) -> bool:
        with self._lock:
            if not self._enabled:
                self._status["state"] = "stopped"
                self._status["message"] = "Scheduler is disabled."
                return False

            if self._thread and self._thread.is_alive():
                return False

            self._stop_event.clear()

            self._thread = threading.Thread(
                target=self._run,
                name="cash-machine-scheduler",
                daemon=True,
            )
            self._thread.start()

            self._status["state"] = "running"
            self._status["message"] = (
                f"Automatic refresh scheduled daily at {self.schedule_label}."
            )

        Logger.info(
            f"Scheduler started: {self.schedule_label} "
            f"({self._timezone.key})"
        )
        return True

    def stop(self) -> None:
        self._stop_event.set()

        with self._lock:
            self._status["state"] = "stopped"
            self._status["message"] = "Scheduler stopped."

    def _run(self) -> None:
        # Check immediately after startup so that a server started after the
        # configured time can still perform the day's catch-up refresh.
        self._check_once()

        while not self._stop_event.wait(self._check_seconds):
            self._check_once()

    def _check_once(self) -> None:
        now = self._now()

        if not self._should_run_today(now):
            return

        started = refresh_service.start(trigger="scheduled")

        if started:
            Logger.info(
                f"Scheduled refresh started for {now.date().isoformat()}."
            )

            with self._lock:
                self._status["message"] = (
                    "Scheduled refresh started. Waiting for the pipeline to finish."
                )
                self._status["last_scheduled_run"] = now.isoformat(
                    timespec="seconds"
                )
        else:
            Logger.info(
                "Scheduled refresh could not start because another refresh "
                "is already running. The scheduler will retry automatically."
            )


scheduler_service = SchedulerService()
