from __future__ import annotations

from database.database import Database


class AlertRepository:
    """Persistence for idempotent Telegram alert delivery."""

    def __init__(self) -> None:
        self.db = Database()

    def exists(
        self,
        opportunity_id: int,
        alert_type: str,
        fingerprint: str,
    ) -> bool:
        row = self.db.conn.execute(
            """
            SELECT 1
            FROM alert_events
            WHERE opportunity_id = ?
              AND alert_type = ?
              AND fingerprint = ?
            LIMIT 1
            """,
            (opportunity_id, alert_type, fingerprint),
        ).fetchone()
        return row is not None

    def record(
        self,
        opportunity_id: int,
        alert_type: str,
        fingerprint: str,
    ) -> int:
        if self.exists(opportunity_id, alert_type, fingerprint):
            row = self.db.conn.execute(
                """
                SELECT id
                FROM alert_events
                WHERE opportunity_id = ?
                  AND alert_type = ?
                  AND fingerprint = ?
                LIMIT 1
                """,
                (opportunity_id, alert_type, fingerprint),
            ).fetchone()
            return int(row[0])

        return self.db.insert_returning_id(
            """
            INSERT INTO alert_events(
                opportunity_id, alert_type, fingerprint
            ) VALUES (?, ?, ?)
            """,
            (opportunity_id, alert_type, fingerprint),
        )

    def close(self) -> None:
        self.db.conn.close()
