from models.analysis import Analysis


class RankingEngine:

    def calculate(self, analysis: Analysis) -> Analysis:

        ranking = (
            analysis.cash_machine_score * 0.50
            + analysis.confidence * 0.20
            + analysis.ai_leverage_score * 10 * 0.10
            + analysis.distribution_score * 10 * 0.10
            + analysis.problem_score * 10 * 0.05
            + analysis.business_score * 10 * 0.05
        )

        ranking = round(max(0, min(100, ranking)))

        analysis.ranking_score = ranking

        if ranking >= 75:
            analysis.portfolio_status = "BUILD"

        elif ranking >= 45:
            analysis.portfolio_status = "WATCH"

        else:
            analysis.portfolio_status = "SKIP"

        return analysis