class AnalysisValidator:

    REQUIRED_FIELDS = {
        "problem": str,
        "customer": str,
        "pain_level": int,
        "urgency": int,
        "current_solution": str,
        "why_current_solution_fails": str,
        "category": str,
        "market_size": str,
        "market_maturity": str,
        "competition_level": int,
        "competition": str,
        "business_model": str,
        "competitive_advantage": str,
        "implementation_difficulty": int,
        "monetization_difficulty": int,
        "confidence": int,
        "opportunity_score": int,
        "reasoning": str,
        "red_flags": str,
        "next_steps": str,
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

                if not 0 <= value <= 10:
                    raise ValueError(
                        f"Field '{field}' must be between 0 and 10."
                    )

            else:

                value = str(value).strip()

                if not value:
                    raise ValueError(
                        f"Field '{field}' cannot be empty."
                    )

            validated[field] = value

        return validated