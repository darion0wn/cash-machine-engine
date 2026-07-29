from models.investment_recommendation import InvestmentRecommendation


class AnalysisValidator:

    REQUIRED_FIELDS = {
        # Problem Analysis
        "problem": str,
        "customer": str,
        "pain_level": int,
        "urgency": int,
        "current_solution": str,
        "why_current_solution_fails": str,

        # Market Analysis
        "category": str,
        "market_size": str,
        "market_maturity": str,
        "competition_level": int,
        "competition": str,

        # Business Analysis
        "business_model": str,
        "competitive_advantage": str,
        "implementation_difficulty": int,
        "monetization_difficulty": int,

        # Investment Evaluation
        "problem_score": int,
        "market_score": int,
        "competition_score": int,
        "business_score": int,
        "execution_score": int,

        "opportunity_score": int,
        "investment_recommendation": str,

        "confidence": int,
        "confidence_reason": str,

        # Explainability
        "reasoning": str,
        "key_evidence": list,
        "red_flags": list,
        "recommended_next_steps": str,
    }

    SCORE_FIELDS = {
        "pain_level",
        "urgency",
        "competition_level",
        "implementation_difficulty",
        "monetization_difficulty",
        "problem_score",
        "market_score",
        "competition_score",
        "business_score",
        "execution_score",
        "confidence",
    }

    @classmethod
    def validate(cls, data: dict) -> dict:

        validated = {}

        for field, expected_type in cls.REQUIRED_FIELDS.items():

            if field not in data:
                raise ValueError(f"Missing required field: '{field}'")

            value = data[field]

            if expected_type is int:

                try:
                    value = int(value)
                except Exception:
                    raise ValueError(
                        f"Field '{field}' must be an integer."
                    )

                if field in cls.SCORE_FIELDS:

                    if not 0 <= value <= 10:
                        raise ValueError(
                            f"Field '{field}' must be between 0 and 10."
                        )

                elif field == "opportunity_score":

                    if not 0 <= value <= 100:
                        raise ValueError(
                            "Field 'opportunity_score' must be between 0 and 100."
                        )

            elif expected_type is list:

                if not isinstance(value, list):
                    raise ValueError(
                        f"Field '{field}' must be a list."
                    )

                value = [str(item).strip() for item in value if str(item).strip()]

            else:

                value = str(value).strip()

                if not value:
                    raise ValueError(
                        f"Field '{field}' cannot be empty."
                    )

                if field == "investment_recommendation":

                    valid_values = {
                        recommendation.value
                        for recommendation in InvestmentRecommendation
                    }

                    if value not in valid_values:
                        raise ValueError(
                            f"Invalid investment recommendation: '{value}'."
                        )

            validated[field] = value

        return validated