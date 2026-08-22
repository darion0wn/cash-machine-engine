from __future__ import annotations

from database.database import Database


def main() -> int:
    db = Database()
    rows = db.conn.execute(
        """
        SELECT opportunity_id, COUNT(*)
        FROM founder_decisions
        WHERE source = 'engine'
        GROUP BY opportunity_id
        HAVING COUNT(*) > 1
        """
    ).fetchall()

    removed = 0
    for opportunity_id, _count in rows:
        decisions = db.conn.execute(
            """
            SELECT id
            FROM founder_decisions
            WHERE opportunity_id = ? AND source = 'engine'
            ORDER BY decided_at DESC, id DESC
            """,
            (opportunity_id,),
        ).fetchall()
        keep_id = decisions[0][0]
        old_ids = [row[0] for row in decisions[1:]]
        if old_ids:
            placeholders = ",".join("?" for _ in old_ids)
            db.conn.execute(
                f"DELETE FROM founder_decisions WHERE id IN ({placeholders})",
                old_ids,
            )
            db.conn.commit()
            removed += len(old_ids)
        print(f"opportunity_id={opportunity_id}: kept={keep_id}, removed={len(old_ids)}")

    print(f"Engine decision cleanup completed: opportunities={len(rows)}, removed={removed}")
    db.conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
