from __future__ import annotations

from database.database import Database


class FavoriteRepository:

    def __init__(self):
        self.db = Database()

    def is_favorite(self, opportunity_id: int) -> bool:
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            SELECT 1
            FROM favorite_opportunities
            WHERE opportunity_id = ?
            LIMIT 1
            """,
            (opportunity_id,),
        )
        return cursor.fetchone() is not None

    def add(
        self,
        opportunity_id: int,
        cash_machine_score: int = 0,
        ranking_score: int = 0,
        portfolio_status: str | None = None,
    ) -> bool:
        cursor = self.db.conn.cursor()

        cursor.execute(
            """
            INSERT INTO favorite_opportunities (
                opportunity_id,
                cash_machine_score_at_save,
                ranking_score_at_save,
                portfolio_status_at_save
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(opportunity_id) DO NOTHING
            """,
            (
                opportunity_id,
                cash_machine_score,
                ranking_score,
                portfolio_status,
            ),
        )

        self.db.conn.commit()
        return cursor.rowcount > 0

    def remove(self, opportunity_id: int) -> bool:
        cursor = self.db.conn.cursor()

        cursor.execute(
            """
            DELETE FROM favorite_opportunities
            WHERE opportunity_id = ?
            """,
            (opportunity_id,),
        )

        self.db.conn.commit()
        return cursor.rowcount > 0

    def toggle(
        self,
        opportunity_id: int,
        cash_machine_score: int = 0,
        ranking_score: int = 0,
        portfolio_status: str | None = None,
    ) -> bool:
        if self.is_favorite(opportunity_id):
            self.remove(opportunity_id)
            return False

        self.add(
            opportunity_id=opportunity_id,
            cash_machine_score=cash_machine_score,
            ranking_score=ranking_score,
            portfolio_status=portfolio_status,
        )
        return True

    def count(self) -> int:
        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM favorite_opportunities"
        )
        return int(cursor.fetchone()[0])

    def list_with_current_analysis(self, limit: int = 100) -> list[dict]:
        cursor = self.db.conn.cursor()

        cursor.execute(
            """
            SELECT
                f.id AS favorite_id,
                f.opportunity_id,
                f.saved_at,
                f.cash_machine_score_at_save,
                f.ranking_score_at_save,
                f.portfolio_status_at_save,

                o.source,
                o.title,
                o.url,

                a.cash_machine_score,
                a.ranking_score,
                a.trend_score,
                a.portfolio_status,
                a.build_verdict,
                a.created_at AS analysis_created_at,
                a.topics,
                a.category,
                a.next_action,
                a.biggest_risk

            FROM favorite_opportunities f

            JOIN opportunities o
              ON o.id = f.opportunity_id

            LEFT JOIN analyses a
              ON a.id = (
                SELECT a2.id
                FROM analyses a2
                WHERE a2.opportunity_id = f.opportunity_id
                ORDER BY a2.created_at DESC, a2.id DESC
                LIMIT 1
              )

            ORDER BY f.saved_at DESC, f.id DESC
            LIMIT ?
            """,
            (limit,),
        )

        columns = [
            description[0]
            for description in (cursor.description or [])
        ]

        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
