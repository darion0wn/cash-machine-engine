from __future__ import annotations

from database.database import Database


class FounderDecisionRepository:

    VALID_DECISIONS = {"BUILD", "VALIDATE", "WATCH", "KILL"}

    def __init__(self) -> None:
        self.db = Database()

    def save(
        self,
        opportunity_id: int,
        decision: str,
        rationale: str,
        next_action: str,
        source: str = "founder",
    ) -> int:
        decision = (decision or "WATCH").upper().strip()
        if decision not in self.VALID_DECISIONS:
            raise ValueError(f"Invalid founder decision: {decision}")
        return self.db.insert_returning_id(
            """
            INSERT INTO founder_decisions(
                opportunity_id, decision, rationale, next_action, source
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                opportunity_id, decision,
                (rationale or "").strip(),
                (next_action or "").strip(),
                (source or "founder").strip(),
            ),
        )

    def latest(self, opportunity_id: int) -> dict | None:
        row = self.db.conn.execute(
            """
            SELECT id, opportunity_id, decision, rationale, next_action,
                   source, decided_at
            FROM founder_decisions
            WHERE opportunity_id = ?
            ORDER BY decided_at DESC, id DESC
            LIMIT 1
            """,
            (opportunity_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "opportunity_id": row[1],
            "decision": row[2],
            "rationale": row[3],
            "next_action": row[4],
            "source": row[5],
            "decided_at": row[6],
        }

    def close(self) -> None:
        self.db.conn.close()
