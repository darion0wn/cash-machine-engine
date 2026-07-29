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
                urgency,
                current_solution,
                why_current_solution_fails,

                category,
                market_size,
                market_maturity,
                competition_level,
                competition,

                business_model,
                competitive_advantage,
                implementation_difficulty,
                monetization_difficulty,

                confidence,
                opportunity_score,
                reasoning,
                red_flags,
                next_steps
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                analysis.opportunity_id,

                analysis.model,
                analysis.prompt_version,

                analysis.problem,
                analysis.customer,
                analysis.pain_level,
                analysis.urgency,
                analysis.current_solution,
                analysis.why_current_solution_fails,

                analysis.category,
                analysis.market_size,
                analysis.market_maturity,
                analysis.competition_level,
                analysis.competition,

                analysis.business_model,
                analysis.competitive_advantage,
                analysis.implementation_difficulty,
                analysis.monetization_difficulty,

                analysis.confidence,
                analysis.opportunity_score,
                analysis.reasoning,
                analysis.red_flags,
                analysis.next_steps,
            ),
        )

        self.db.conn.commit()

        return cursor.lastrowid