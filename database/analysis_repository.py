import json

from database.database import Database
from models.analysis import Analysis
from models.investment_recommendation import InvestmentRecommendation


class AnalysisRepository:

    def __init__(self, db: Database | None = None):
        self.db = db or Database()
        self._owns_db = db is None

    def save(self, analysis: Analysis) -> int:

        return self.db.insert_returning_id(
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

                topics,

                trend_score,

                ranking_score,

                portfolio_status,

                recommended_next_steps

            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
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

                json.dumps(analysis.topics or []),

                analysis.trend_score,

                analysis.ranking_score,

                analysis.portfolio_status,

                analysis.recommended_next_steps,
            ),
        )
    
    def find_all(self):

        cursor = self.db.conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM analyses
            ORDER BY id
            """
        )

        rows = cursor.fetchall()

        analyses = []

        columns = [description[0] for description in cursor.description]

        for row in rows:

            data = dict(zip(columns, row))

            data["key_evidence"] = json.loads(
                data["key_evidence"]
            )

            data["red_flags"] = json.loads(
                data["red_flags"]
            )

            topics = data.get("topics") or "[]"

            if isinstance(topics, str):

                try:
                    topics = json.loads(topics)
                except Exception:
                    topics = []

            if not isinstance(topics, list):
                topics = []

            data["topics"] = [
                str(item).strip()
                for item in topics
                if str(item).strip()
            ]

            recommendation = data.get("investment_recommendation")

            if isinstance(recommendation, str):
                data["investment_recommendation"] = (
                    InvestmentRecommendation(recommendation)
                )

            analyses.append(
                Analysis(**data)
            )

        return analyses

    def update_ranking(
        self,
        analysis_id: int,
        ranking_score: int,
        portfolio_status: str,
    ):

        cursor = self.db.conn.cursor()

        cursor.execute(
            """
            UPDATE analyses

            SET

                ranking_score = ?,

                portfolio_status = ?

            WHERE id = ?
            """,
            (
                ranking_score,
                portfolio_status,
                analysis_id,
            ),
        )

        self.db.conn.commit()
    def close(self):
        if self._owns_db:
            self.db.conn.close()
