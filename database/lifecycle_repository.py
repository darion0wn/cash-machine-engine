from __future__ import annotations

from database.database import Database


class LifecycleRepository:
    VALID_STAGES = {
        "DISCOVERED",
        "ANALYZED",
        "VALIDATING",
        "VALIDATED",
        "BUILDING",
        "LAUNCHED",
        "REVENUE_500",
        "KILLED",
    }

    def __init__(self) -> None:
        self.db = Database()

    def current(self, opportunity_id: int) -> dict | None:
        row = self.db.conn.execute(
            """
            SELECT id, opportunity_id, stage, reason, source, changed_at
            FROM opportunity_lifecycle
            WHERE opportunity_id = ?
            ORDER BY changed_at DESC, id DESC
            LIMIT 1
            """,
            (opportunity_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "opportunity_id": row[1],
            "stage": row[2],
            "reason": row[3],
            "source": row[4],
            "changed_at": row[5],
        }

    def history(self, opportunity_id: int, limit: int = 12) -> list[dict]:
        rows = self.db.conn.execute(
            """
            SELECT id, opportunity_id, stage, reason, source, changed_at
            FROM opportunity_lifecycle
            WHERE opportunity_id = ?
            ORDER BY changed_at DESC, id DESC
            LIMIT ?
            """,
            (opportunity_id, limit),
        ).fetchall()
        return [
            {
                "id": row[0],
                "opportunity_id": row[1],
                "stage": row[2],
                "reason": row[3],
                "source": row[4],
                "changed_at": row[5],
            }
            for row in rows
        ]

    def save(
        self,
        opportunity_id: int,
        stage: str,
        reason: str,
        source: str = "founder",
    ) -> int:
        stage = (stage or "ANALYZED").upper().strip()
        if stage not in self.VALID_STAGES:
            raise ValueError(f"Invalid lifecycle stage: {stage}")
        current = self.current(opportunity_id)
        if current and current["stage"] == stage:
            return int(current["id"])
        return self.db.insert_returning_id(
            """
            INSERT INTO opportunity_lifecycle(
                opportunity_id, stage, reason, source
            ) VALUES (?, ?, ?, ?)
            """,
            (
                opportunity_id,
                stage,
                (reason or "").strip(),
                (source or "founder").strip(),
            ),
        )

    def close(self) -> None:
        self.db.conn.close()
