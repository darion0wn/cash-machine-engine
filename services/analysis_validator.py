from models.investment_recommendation import InvestmentRecommendation


class AnalysisValidator:

    REQUIRED_FIELDS = {

        # Problem Analysis
        "problem": str,
        "customer": str,
        "ideal_customer": str,

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
        "pricing_strategy": str,

        "competitive_advantage": str,

        "mvp_description": str,

        "implementation_difficulty": int,
        "monetization_difficulty": int,

        # Scores
        "problem_score": int,
        "market_score": int,
        "competition_score": int,
        "business_score": int,
        "execution_score": int,

        "ai_leverage_score": int,
        "distribution_score": int,

        "cash_machine_score": int,

        "build_verdict": str,

        # Legacy compatibility
        "investment_recommendation": str,

        "confidence": int,
        "confidence_reason": str,

        # Explainability
        "reasoning": str,

        "key_evidence": list,

        "red_flags": list,

        "biggest_risk": str,

        "next_action": str,

        "recommended_next_steps": str,

        "topics": list,
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

        "ai_leverage_score",
        "distribution_score",

        "confidence",
    }

    @classmethod
    def validate(
        cls,
        data: dict,
    ) -> dict:

        validated = {}

        #
        # Retrocompatibilità
        #

        if (
            "cash_machine_score" in data
            and "opportunity_score" not in data
        ):

            data["opportunity_score"] = data[
                "cash_machine_score"
            ]

        if (
            "build_verdict" in data
            and "investment_recommendation" not in data
        ):

            mapping = {
                "BUILD": "BUY",
                "WATCH": "WATCH",
                "SKIP": "PASS",
            }

            data["investment_recommendation"] = mapping.get(
                data["build_verdict"],
                "WATCH",
            )

        for field, expected_type in cls.REQUIRED_FIELDS.items():

            if field not in data:

                raise ValueError(
                    f"Missing required field: '{field}'"
                )

            value = data[field]

            if expected_type is int:

                try:

                    value = int(value)

                except Exception:

                    raise ValueError(
                        f"Field '{field}' must be an integer."
                    )

                if field == "cash_machine_score":

                    if not 0 <= value <= 100:

                        raise ValueError(
                            "cash_machine_score must be between 0 and 100."
                        )

                elif field in cls.SCORE_FIELDS:

                    if not 0 <= value <= 10:

                        raise ValueError(
                            f"Field '{field}' must be between 0 and 10."
                        )

            elif expected_type is list:

                if value is None:
                    value = []
                elif isinstance(value, str):
                    value = [value]
                elif isinstance(value, tuple):
                    value = list(value)
                elif not isinstance(value, list):
                    value = [str(value)]

                cleaned = []
                seen = set()

                for item in value:

                    item = str(item).strip()

                    if not item:
                        continue

                    key = item.lower()

                    if key in seen:
                        continue

                    seen.add(key)
                    cleaned.append(item)

                value = cleaned

                if field == "topics":
                    value = cleaned[:5]
                else:
                    value = cleaned

            else:

                value = str(value).strip()

                if not value:
                    raise ValueError(
                        f"Field '{field}' cannot be empty."
                    )

                if field == "investment_recommendation":
                    mapping={"BUILD":"BUY","WATCH":"WATCH","SKIP":"PASS","BUY":"BUY","PASS":"PASS"}
                    value=mapping.get(value.upper(),value)
                    valid_values={r.value for r in InvestmentRecommendation}
                    if value not in valid_values:
                        raise ValueError(
                            f"Invalid investment recommendation: '{value}'."
                        )

            validated[field] = value

        #
        # Compatibilità col repository esistente
        #

        validated["opportunity_score"] = validated[
            "cash_machine_score"
        ]

        return validated