from __future__ import annotations

import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path


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
        }

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def get_status(self) -> dict:
        with self._lock:
            return dict(self._status)

    def start(self) -> bool:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return False

            self._status = {
                "state": "running",
                "started_at": self._now(),
                "finished_at": None,
                "return_code": None,
                "message": "Crawler and analysis worker are running.",
            }

            self._thread = threading.Thread(
                target=self._run,
                name="cash-machine-refresh",
                daemon=True,
            )
            self._thread.start()

            return True

    def _run(self) -> None:
        root_dir = Path(__file__).resolve().parents[2]

        try:
            completed = subprocess.run(
                [sys.executable, "-m", "crawler.main"],
                cwd=str(root_dir),
                check=False,
            )

            with self._lock:
                self._status["state"] = (
                    "completed" if completed.returncode == 0 else "failed"
                )
                self._status["finished_at"] = self._now()
                self._status["return_code"] = completed.returncode
                self._status["message"] = (
                    "Refresh completed successfully."
                    if completed.returncode == 0
                    else "Refresh finished with an error."
                )

        except Exception as exc:
            with self._lock:
                self._status["state"] = "failed"
                self._status["finished_at"] = self._now()
                self._status["return_code"] = None
                self._status["message"] = f"Refresh failed: {exc}"


refresh_service = RefreshService()
