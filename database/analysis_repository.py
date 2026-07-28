from database.database import Database
from models.analysis import Analysis


class AnalysisRepository:

    def __init__(self):
        self.db = Database()

    def save(self, analysis: Analysis) -> int:

        cursor = self.db.conn.cursor()

        cursor.execute(
            """
            INSERT INTO analyses (
                opportunity_id,
                model,
                prompt_version,
                problem,
                customer,
                pain_level,
                market_size,
                opportunity_score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                analysis.opportunity_id,
                analysis.model,
                analysis.prompt_version,
                analysis.problem,
                analysis.customer,
                analysis.pain_level,
                analysis.market_size,
                analysis.opportunity_score,
            ),
        )

        self.db.conn.commit()

        return cursor.lastrowid