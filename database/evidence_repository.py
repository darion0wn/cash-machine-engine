from __future__ import annotations

from database.database import Database


class EvidenceRepository:

    VALID_STATUSES = {"PASS", "FAIL", "PARTIAL"}
    VALID_CONFIDENCE = {"LOW", "MEDIUM", "HIGH"}

    def __init__(self) -> None:
        self.db = Database()

    def add(
        self,
        opportunity_id: int,
        validation_key: str,
        status: str,
        observation: str,
        source: str | None = None,
        confidence: str = "MEDIUM",
        notes: str | None = None,
    ) -> int:
        status = (status or "PARTIAL").upper().strip()
        confidence = (confidence or "MEDIUM").upper().strip()

        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid evidence status: {status}")
        if confidence not in self.VALID_CONFIDENCE:
            raise ValueError(f"Invalid evidence confidence: {confidence}")
        if not validation_key or not validation_key.strip():
            raise ValueError("validation_key is required")
        if not observation or not observation.strip():
            raise ValueError("observation is required")

        cursor = self.db.conn.execute(
            """
            INSERT INTO validation_evidence(
                opportunity_id, validation_key, status, observation,
                source, confidence, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                opportunity_id, validation_key.strip(), status,
                observation.strip(), (source or "").strip() or None,
                confidence, (notes or "").strip() or None,
            ),
        )
        self.db.conn.commit()
        return int(cursor.lastrowid)

    def list_for_opportunity(self, opportunity_id: int) -> list[dict]:
        rows = self.db.conn.execute(
            """
            SELECT
                id, opportunity_id, validation_key, status, observation,
                source, confidence, notes, captured_at
            FROM validation_evidence
            WHERE opportunity_id = ?
            ORDER BY captured_at DESC, id DESC
            """,
            (opportunity_id,),
        ).fetchall()

        return [
            {
                "id": row[0],
                "opportunity_id": row[1],
                "validation_key": row[2],
                "status": row[3],
                "observation": row[4],
                "source": row[5] or "",
                "confidence": row[6],
                "notes": row[7] or "",
                "captured_at": row[8],
            }
            for row in rows
        ]

    def latest_by_key(self, opportunity_id: int) -> dict[str, dict]:
        result: dict[str, dict] = {}
        for item in self.list_for_opportunity(opportunity_id):
            result.setdefault(item["validation_key"], item)
        return result

    def count_by_status(self, opportunity_id: int) -> dict[str, int]:
        rows = self.db.conn.execute(
            """
            SELECT status, COUNT(*)
            FROM validation_evidence
            WHERE opportunity_id = ?
            GROUP BY status
            """,
            (opportunity_id,),
        ).fetchall()
        result = {status: 0 for status in self.VALID_STATUSES}
        for status, count in rows:
            result[status] = int(count)
        return result

    def close(self) -> None:
        self.db.conn.close()
