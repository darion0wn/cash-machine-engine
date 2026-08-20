from __future__ import annotations

import threading
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from config.settings import (
    SCHEDULER_CATCH_UP,
    SCHEDULER_CHECK_SECONDS,
    SCHEDULER_ENABLED,
    SCHEDULER_TIMES,
    SCHEDULER_TIMEZONE,
)
from core.logger import Logger
from database.database import Database
from web.services.refresh_service import refresh_service


class SchedulerService:
    """Runs automatic refreshes at the configured daily time slots."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        self._enabled = bool(SCHEDULER_ENABLED)
        self._times = self._parse_times(SCHEDULER_TIMES)
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
    def _parse_times(values: list[str]) -> list[tuple[int, int]]:
        parsed: list[tuple[int, int]] = []

        for value in values:
            try:
                hour_text, minute_text = value.strip().split(":", 1)
                hour = int(hour_text)
                minute = int(minute_text)

                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError

                parsed.append((hour, minute))
            except (AttributeError, ValueError):
                Logger.warning(
                    f"Invalid scheduler time '{value}'. Ignoring this slot."
                )

        if not parsed:
            Logger.warning(
                "No valid scheduler times configured. Falling back to 07:00."
            )
            parsed = [(7, 0)]

        return sorted(set(parsed))

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
        slots = ", ".join(f"{hour:02d}:{minute:02d}" for hour, minute in self._times)
        return f"{slots} daily"

    def _now(self) -> datetime:
        return datetime.now(self._timezone)

    def _scheduled_datetime(
        self,
        target_date: date,
        slot: tuple[int, int],
    ) -> datetime:
        hour, minute = slot
        return datetime(
            target_date.year,
            target_date.month,
            target_date.day,
            hour,
            minute,
            tzinfo=self._timezone,
        )

    @staticmethod
    def _trigger_for_slot(slot: tuple[int, int]) -> str:
        hour, minute = slot
        return f"scheduled:{hour:02d}:{minute:02d}"

    def _next_run(self) -> datetime:
        now = self._now()

        for slot in self._times:
            candidate = self._scheduled_datetime(now.date(), slot)
            if candidate > now:
                return candidate

        return self._scheduled_datetime(
            now.date() + timedelta(days=1),
            self._times[0],
        )

    @staticmethod
    def _get_scheduled_run_today(
        target_date: date,
        trigger: str | None = None,
    ) -> dict | None:
        db = Database()

        # Compare a full day range instead of applying SQLite's substr() to
        # a timestamp. PostgreSQL stores started_at as TIMESTAMP, while
        # SQLite stores it as a DATETIME/text value. Range comparisons work
        # correctly with both backends and preserve index-friendly filtering.
        day_start = datetime.combine(target_date, datetime.min.time())
        day_end = day_start + timedelta(days=1)

        try:
            if trigger is None:
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
                    WHERE started_at >= ?
                      AND started_at < ?
                      AND trigger LIKE ?
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (day_start, day_end, "scheduled:%"),
                ).fetchone()
            else:
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
                    WHERE started_at >= ?
                      AND started_at < ?
                      AND trigger = ?
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (day_start, day_end, trigger),
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

    def _slot_has_run_today(
        self,
        target_date: date,
        slot: tuple[int, int],
    ) -> bool:
        trigger = self._trigger_for_slot(slot)
        return self._get_scheduled_run_today(target_date, trigger) is not None

    def _due_slot(self, now: datetime) -> tuple[int, int] | None:
        due_slots = [
            slot
            for slot in self._times
            if self._scheduled_datetime(now.date(), slot) <= now
        ]

        if not due_slots:
            return None

        # Run the latest due slot. This avoids replaying every missed slot
        # after a deployment/restart while still supporting catch-up.
        for slot in reversed(due_slots):
            if self._slot_has_run_today(now.date(), slot):
                continue

            scheduled_at = self._scheduled_datetime(now.date(), slot)

            if self._catch_up or now <= scheduled_at + timedelta(minutes=1):
                return slot

        return None

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

        with self._lock:
            status = dict(self._status)

        status["next_run"] = self._next_run().isoformat(timespec="seconds")

        scheduled_today = self._get_scheduled_run_today(now.date())
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
                f"Automatic refresh scheduled at {self.schedule_label}."
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
        self._check_once()

        while not self._stop_event.wait(self._check_seconds):
            self._check_once()

    def _check_once(self) -> None:
        now = self._now()
        slot = self._due_slot(now)

        if slot is None:
            return

        trigger = self._trigger_for_slot(slot)
        started = refresh_service.start(trigger=trigger)

        if started:
            Logger.info(
                f"Scheduled refresh started for {now.date().isoformat()} "
                f"at {slot[0]:02d}:{slot[1]:02d}."
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
