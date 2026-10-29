from models.analysis import Analysis


class RankingEngine:
    """Calculate a deterministic portfolio ranking from an AI analysis.

    Every component is normalized to a 0-100 scale before its configured
    weight is applied. ``portfolio_status`` is derived from this ranking;
    ``build_verdict`` remains the separate verdict produced by the AI analysis.
    """

    WEIGHTS = {
        "cash_machine_score": 0.50,
        "confidence": 0.20,
        "ai_leverage_score": 0.10,
        "distribution_score": 0.10,
        "problem_score": 0.05,
        "business_score": 0.05,
    }
    BUILD_THRESHOLD = 75
    WATCH_THRESHOLD = 45

    @staticmethod
    def _bounded_score(value, maximum: float = 10.0) -> float:
        """Convert a component to a bounded 0-maximum numeric value."""
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = 0.0
        return max(0.0, min(maximum, number))

    def calculate(self, analysis: Analysis) -> Analysis:
        cash_machine = self._bounded_score(analysis.cash_machine_score, 100.0)
        confidence = self._bounded_score(analysis.confidence)
        ai_leverage = self._bounded_score(analysis.ai_leverage_score)
        distribution = self._bounded_score(analysis.distribution_score)
        problem = self._bounded_score(analysis.problem_score)
        business = self._bounded_score(analysis.business_score)

        ranking = (
            cash_machine * self.WEIGHTS["cash_machine_score"]
            + (confidence / 10.0 * 100.0) * self.WEIGHTS["confidence"]
            + (ai_leverage / 10.0 * 100.0) * self.WEIGHTS["ai_leverage_score"]
            + (distribution / 10.0 * 100.0) * self.WEIGHTS["distribution_score"]
            + (problem / 10.0 * 100.0) * self.WEIGHTS["problem_score"]
            + (business / 10.0 * 100.0) * self.WEIGHTS["business_score"]
        )

        ranking = int(round(max(0.0, min(100.0, ranking))))
        analysis.ranking_score = ranking

        if ranking >= self.BUILD_THRESHOLD:
            analysis.portfolio_status = "BUILD"
        elif ranking >= self.WATCH_THRESHOLD:
            analysis.portfolio_status = "WATCH"
        else:
            analysis.portfolio_status = "SKIP"

        return analysis
