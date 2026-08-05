import json

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
                ideal_customer,

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
                pricing_strategy,

                competitive_advantage,

                mvp_description,

                implementation_difficulty,
                monetization_difficulty,

                problem_score,
                market_score,
                competition_score,
                business_score,
                execution_score,

                ai_leverage_score,
                distribution_score,

                cash_machine_score,

                opportunity_score,

                build_verdict,

                investment_recommendation,

                confidence,
                confidence_reason,

                reasoning,

                key_evidence,
                red_flags,

                biggest_risk,

                next_action,

                recommended_next_steps

            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                analysis.opportunity_id,

                analysis.model,
                analysis.prompt_version,

                analysis.problem,
                analysis.customer,
                analysis.ideal_customer,

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
                analysis.pricing_strategy,

                analysis.competitive_advantage,

                analysis.mvp_description,

                analysis.implementation_difficulty,
                analysis.monetization_difficulty,

                analysis.problem_score,
                analysis.market_score,
                analysis.competition_score,
                analysis.business_score,
                analysis.execution_score,

                analysis.ai_leverage_score,
                analysis.distribution_score,

                analysis.cash_machine_score,

                # Compatibilità con il codice esistente
                analysis.cash_machine_score,

                analysis.build_verdict,

                analysis.investment_recommendation.value,

                analysis.confidence,
                analysis.confidence_reason,

                analysis.reasoning,

                json.dumps(analysis.key_evidence),

                json.dumps(analysis.red_flags),

                analysis.biggest_risk,

                analysis.next_action,

                analysis.recommended_next_steps,
            ),
        )

        self.db.conn.commit()

        return cursor.lastrowid