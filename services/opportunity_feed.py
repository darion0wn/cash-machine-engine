from database.database import Database


class OpportunityFeed:

    def __init__(self):
        self.db = Database()

    def top(self, limit: int = 20):

        cursor = self.db.conn.cursor()

        cursor.execute(
            """
            SELECT

                opportunities.id,

                opportunities.title,

                opportunities.source,

                analyses.cash_machine_score,

                analyses.ranking_score,

                analyses.portfolio_status,

                analyses.build_verdict

            FROM analyses

            JOIN opportunities

            ON opportunities.id = analyses.opportunity_id

            WHERE analyses.ranking_score > 0

            ORDER BY

                analyses.ranking_score DESC,

                analyses.cash_machine_score DESC

            LIMIT ?
            """,
            (limit,),
        )

        rows = cursor.fetchall()

        result = []

        for row in rows:

            result.append(
                {
                    "id": row[0],
                    "title": row[1],
                    "source": row[2],
                    "cash_machine_score": row[3],
                    "ranking_score": row[4],
                    "portfolio_status": row[5],
                    "build_verdict": row[6],
                }
            )

        return result

    def builds(self):

        return [
            x
            for x in self.top(100)
            if x["portfolio_status"] == "BUILD"
        ]

    def watchlist(self):

        return [
            x
            for x in self.top(100)
            if x["portfolio_status"] == "WATCH"
        ]

    def skipped(self):

        return [
            x
            for x in self.top(100)
            if x["portfolio_status"] == "SKIP"
        ]