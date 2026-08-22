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

    def save_engine(
        self,
        opportunity_id: int,
        decision: str,
        rationale: str,
        next_action: str,
    ) -> dict:
        """Upsert the single automatic engine decision for an opportunity.

        Founder decisions are intentionally stored as history, but automatic
        engine decisions are a current state. Keeping one engine row per
        opportunity prevents repeated refreshes/backfills from accumulating
        duplicate engine decisions.
        """
        decision = (decision or "WATCH").upper().strip()
        if decision not in self.VALID_DECISIONS:
            raise ValueError(f"Invalid founder decision: {decision}")

        rationale = (rationale or "").strip()
        next_action = (next_action or "").strip()

        row = self.db.conn.execute(
            """
            SELECT id
            FROM founder_decisions
            WHERE opportunity_id = ? AND source = 'engine'
            ORDER BY decided_at DESC, id DESC
            LIMIT 1
            """,
            (opportunity_id,),
        ).fetchone()

        if row is None:
            decision_id = self.db.insert_returning_id(
                """
                INSERT INTO founder_decisions(
                    opportunity_id, decision, rationale, next_action, source
                ) VALUES (?, ?, ?, ?, 'engine')
                """,
                (opportunity_id, decision, rationale, next_action),
            )
        else:
            decision_id = int(row[0])
            self.db.conn.execute(
                """
                UPDATE founder_decisions
                SET decision = ?, rationale = ?, next_action = ?,
                    decided_at = CURRENT_TIMESTAMP, source = 'engine'
                WHERE id = ?
                """,
                (decision, rationale, next_action, decision_id),
            )
            self.db.conn.commit()

        row = self.db.conn.execute(
            """
            SELECT id, opportunity_id, decision, rationale, next_action,
                   source, decided_at
            FROM founder_decisions
            WHERE id = ?
            """,
            (decision_id,),
        ).fetchone()
        return {
            "id": row[0],
            "opportunity_id": row[1],
            "decision": row[2],
            "rationale": row[3],
            "next_action": row[4],
            "source": row[5],
            "decided_at": row[6],
        }

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
