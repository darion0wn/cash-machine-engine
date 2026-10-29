import unittest
from types import SimpleNamespace

from services.ranking_engine import RankingEngine


def analysis(**overrides):
    values = {
        "cash_machine_score": 50,
        "confidence": 5,
        "ai_leverage_score": 5,
        "distribution_score": 5,
        "problem_score": 5,
        "business_score": 5,
        "ranking_score": 0,
        "portfolio_status": "WATCH",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class RankingEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = RankingEngine()

    def test_confidence_is_normalized_from_zero_to_ten(self):
        low = analysis(confidence=0)
        high = analysis(confidence=10)
        self.engine.calculate(low)
        self.engine.calculate(high)
        self.assertEqual(high.ranking_score - low.ranking_score, 20)

    def test_all_component_weights_produce_expected_score(self):
        item = analysis(
            cash_machine_score=80,
            confidence=8,
            ai_leverage_score=7,
            distribution_score=6,
            problem_score=5,
            business_score=4,
        )
        self.engine.calculate(item)
        self.assertEqual(item.ranking_score, 74)

    def test_maximum_valid_component_scores_reach_100(self):
        item = analysis(
            cash_machine_score=100,
            confidence=10,
            ai_leverage_score=10,
            distribution_score=10,
            problem_score=10,
            business_score=10,
        )
        self.engine.calculate(item)
        self.assertEqual(item.ranking_score, 100)

    def test_result_is_clamped_to_zero_and_100(self):
        item = analysis(cash_machine_score=-20, confidence=-3, ai_leverage_score=-1,
                        distribution_score=-1, problem_score=-1, business_score=-1)
        self.engine.calculate(item)
        self.assertEqual(item.ranking_score, 0)
        item = analysis(cash_machine_score=500, confidence=30, ai_leverage_score=30,
                        distribution_score=30, problem_score=30, business_score=30)
        self.engine.calculate(item)
        self.assertEqual(item.ranking_score, 100)

    def test_build_threshold_is_inclusive(self):
        item = analysis(cash_machine_score=100, confidence=10, ai_leverage_score=5,
                        distribution_score=0, problem_score=0, business_score=0)
        self.engine.calculate(item)
        self.assertEqual(item.portfolio_status, "BUILD")
        self.assertEqual(item.ranking_score, 75)

    def test_watch_threshold_is_inclusive(self):
        item = analysis(cash_machine_score=40, confidence=0, ai_leverage_score=0,
                        distribution_score=0, problem_score=0, business_score=0)
        self.engine.calculate(item)
        self.assertEqual(item.ranking_score, 20)
        self.assertEqual(item.portfolio_status, "SKIP")
        item = analysis(cash_machine_score=90, confidence=0, ai_leverage_score=0,
                        distribution_score=0, problem_score=0, business_score=0)
        self.engine.calculate(item)
        self.assertEqual(item.ranking_score, 45)
        self.assertEqual(item.portfolio_status, "WATCH")

    def test_score_below_watch_threshold_is_skip(self):
        item = analysis(cash_machine_score=80, confidence=0, ai_leverage_score=0,
                        distribution_score=0, problem_score=0, business_score=0)
        self.engine.calculate(item)
        self.assertEqual(item.ranking_score, 40)
        self.assertEqual(item.portfolio_status, "SKIP")

    def test_calculate_returns_original_analysis_and_preserves_ai_verdict(self):
        item = analysis(build_verdict="BUILD", id=42)
        result = self.engine.calculate(item)
        self.assertIs(result, item)
        self.assertEqual(item.build_verdict, "BUILD")


if __name__ == "__main__":
    unittest.main()
