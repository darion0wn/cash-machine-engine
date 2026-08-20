from __future__ import annotations

import re
from typing import Any


class OpportunityValidationFramework:
    """
    Deterministic analysis-quality layer for the private founder workspace.

    This layer does not predict business success and does not trigger a
    second validation cycle. It measures how complete and well-supported the
    existing AI analysis is across the dimensions that matter for the
    opportunity.

    It is informational: unknown dimensions remain UNKNOWN instead of
    creating mandatory founder tasks or blocking the AI verdict.

    Each dimension is classified as:
      - EVIDENCE: directly supported by the stored analysis/context.
      - INFERENCE: derived from an existing scored/structured assessment.
      - UNKNOWN: not sufficiently supported by the current data.
    """

    DIMENSIONS = (
        "problem_severity",
        "target_customer_clarity",
        "willingness_to_pay",
        "market_size",
        "competition",
        "distribution",
        "technical_complexity",
        "time_to_mvp",
        "monetization_potential",
        "ai_leverage",
    )

    _UNKNOWN_VALUES = {"", "unknown", "n/a", "na", "not available", "none"}
    _PRICE_PATTERN = re.compile(
        r"(?i)(?:€|eur|\$|usd|£|gbp)\s*\d+(?:[.,]\d+)?"
        r"|\d+(?:[.,]\d+)?\s*(?:€|eur|\$|usd|£|gbp)"
    )

    @classmethod
    def _known_text(cls, value: Any) -> bool:
        if value is None:
            return False
        return str(value).strip().lower() not in cls._UNKNOWN_VALUES

    @staticmethod
    def _num(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @classmethod
    def _pricing_evidence(cls, text: str | None) -> bool:
        text = str(text or "").strip()
        if not text:
            return False
        return bool(cls._PRICE_PATTERN.search(text))

    @classmethod
    def _dimension(cls, key: str, score: float | None, status: str, reason: str, basis: list[str]) -> dict[str, Any]:
        return {
            "key": key,
            "label": key.replace("_", " ").title(),
            "score": None if score is None else int(round(max(0.0, min(10.0, score)))),
            "status": status,
            "reason": reason,
            "basis": basis,
        }

    @classmethod
    def evaluate(
        cls,
        analysis: dict[str, Any] | None,
        automatic_evidence: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if not analysis:
            return {
                "validation_score": 0,
                "coverage_score": 0,
                "confidence": "Low",
                "known_dimensions": 0,
                "total_dimensions": len(cls.DIMENSIONS),
                "evidence": [],
                "inference": [],
                "unknown": [],
                "dimensions": [],
                "summary": "No completed analysis is available yet.",
                "automatic_evidence_count": 0,
            }

        dimensions: list[dict[str, Any]] = []

        pain = cls._num(analysis.get("pain_level"))
        urgency = cls._num(analysis.get("urgency"))
        problem_text = analysis.get("problem")
        problem_score = cls._num(analysis.get("problem_score"))
        if cls._known_text(problem_text) and (pain > 0 or urgency > 0):
            dimensions.append(cls._dimension(
                "problem_severity",
                (pain + urgency) / 2,
                "EVIDENCE",
                "The analysis includes a concrete problem plus pain/urgency signals.",
                ["problem", "pain_level", "urgency"],
            ))
        elif cls._known_text(problem_text):
            dimensions.append(cls._dimension(
                "problem_severity",
                problem_score,
                "INFERENCE",
                "Problem severity is available through the model's problem score, but supporting pain/urgency detail is incomplete.",
                ["problem", "problem_score"],
            ))
        else:
            dimensions.append(cls._dimension(
                "problem_severity", None, "UNKNOWN", "A concrete problem is not sufficiently described.", []
            ))

        customer = analysis.get("customer")
        ideal_customer = analysis.get("ideal_customer")
        customer_known = cls._known_text(customer)
        ideal_known = cls._known_text(ideal_customer)
        if customer_known and ideal_known:
            dimensions.append(cls._dimension(
                "target_customer_clarity",
                9.0,
                "EVIDENCE",
                "Both the customer and ideal customer profile are explicitly described.",
                ["customer", "ideal_customer"],
            ))
        elif customer_known or ideal_known:
            dimensions.append(cls._dimension(
                "target_customer_clarity",
                6.0,
                "EVIDENCE",
                "A customer segment is identified, but the profile is incomplete.",
                ["customer" if customer_known else "ideal_customer"],
            ))
        else:
            dimensions.append(cls._dimension(
                "target_customer_clarity", None, "UNKNOWN", "No reliable customer segment is identified.", []
            ))

        pricing = analysis.get("pricing_strategy")
        business_model = analysis.get("business_model")
        if cls._pricing_evidence(pricing):
            dimensions.append(cls._dimension(
                "willingness_to_pay",
                None,
                "UNKNOWN",
                "Explicit pricing evidence exists, but willingness to pay has not been validated with real customers.",
                ["pricing_strategy"],
            ))
        elif cls._known_text(pricing) or cls._known_text(business_model):
            dimensions.append(cls._dimension(
                "willingness_to_pay",
                None,
                "UNKNOWN",
                "A monetization approach is described, but no concrete willingness-to-pay evidence is available.",
                [field for field, value in (("pricing_strategy", pricing), ("business_model", business_model)) if cls._known_text(value)],
            ))
        else:
            dimensions.append(cls._dimension(
                "willingness_to_pay", None, "UNKNOWN", "No willingness-to-pay evidence is available.", []
            ))

        market_size = analysis.get("market_size")
        if cls._known_text(market_size):
            dimensions.append(cls._dimension(
                "market_size",
                7.0,
                "EVIDENCE",
                "The analysis contains an explicit market-size assessment.",
                ["market_size"],
            ))
        else:
            dimensions.append(cls._dimension(
                "market_size", None, "UNKNOWN", "Market size is not sufficiently established.", []
            ))

        competition = analysis.get("competition")
        competition_level = cls._num(analysis.get("competition_level"))
        if cls._known_text(competition) and competition_level > 0:
            dimensions.append(cls._dimension(
                "competition",
                max(0.0, 10.0 - competition_level + 1.0),
                "EVIDENCE",
                "Competition is described and a competition level is available.",
                ["competition", "competition_level"],
            ))
        elif cls._known_text(competition):
            dimensions.append(cls._dimension(
                "competition",
                5.0,
                "EVIDENCE",
                "Competition is described, but there is no numeric competition level.",
                ["competition"],
            ))
        else:
            dimensions.append(cls._dimension(
                "competition", None, "UNKNOWN", "Competitive conditions are not sufficiently described.", []
            ))

        distribution = cls._num(analysis.get("distribution_score"))
        if distribution > 0:
            dimensions.append(cls._dimension(
                "distribution",
                distribution,
                "INFERENCE",
                "Distribution strength is inferred from the existing distribution score.",
                ["distribution_score"],
            ))
        else:
            dimensions.append(cls._dimension(
                "distribution", None, "UNKNOWN", "There is not enough evidence to assess distribution.", []
            ))

        implementation = cls._num(analysis.get("implementation_difficulty"))
        if implementation > 0:
            dimensions.append(cls._dimension(
                "technical_complexity",
                max(0.0, 11.0 - implementation),
                "INFERENCE",
                "Technical feasibility is inferred from implementation difficulty.",
                ["implementation_difficulty"],
            ))
        else:
            dimensions.append(cls._dimension(
                "technical_complexity", None, "UNKNOWN", "Technical complexity is not sufficiently assessed.", []
            ))

        mvp_description = analysis.get("mvp_description")
        if cls._known_text(mvp_description):
            mvp_score = max(1.0, min(10.0, 11.0 - implementation)) if implementation > 0 else 6.0
            dimensions.append(cls._dimension(
                "time_to_mvp",
                mvp_score,
                "INFERENCE",
                "MVP feasibility is inferred from the existence of a concrete MVP description and implementation difficulty.",
                ["mvp_description", "implementation_difficulty"],
            ))
        else:
            dimensions.append(cls._dimension(
                "time_to_mvp", None, "UNKNOWN", "The MVP is not described well enough to estimate time to MVP.", []
            ))

        monetization_difficulty = cls._num(analysis.get("monetization_difficulty"))
        if monetization_difficulty > 0:
            dimensions.append(cls._dimension(
                "monetization_potential",
                max(0.0, 11.0 - monetization_difficulty),
                "INFERENCE",
                "Monetization potential is inferred from the existing monetization difficulty score.",
                ["monetization_difficulty", "business_model"],
            ))
        else:
            dimensions.append(cls._dimension(
                "monetization_potential", None, "UNKNOWN", "There is not enough evidence to assess monetization potential.", []
            ))

        ai_leverage = cls._num(analysis.get("ai_leverage_score"))
        if ai_leverage > 0:
            dimensions.append(cls._dimension(
                "ai_leverage",
                ai_leverage,
                "INFERENCE",
                "AI leverage is inferred from the existing AI leverage score.",
                ["ai_leverage_score"],
            ))
        else:
            dimensions.append(cls._dimension(
                "ai_leverage", None, "UNKNOWN", "AI leverage has not been sufficiently assessed.", []
            ))

        automatic_evidence = automatic_evidence or {}
        evidence_status_score = {"PASS": 10, "PARTIAL": 5, "FAIL": 0}
        for item in dimensions:
            evidence = automatic_evidence.get(item.get("key"))
            if not evidence:
                continue
            status = str(evidence.get("status") or "PARTIAL").upper()
            if status not in evidence_status_score:
                continue
            evidence_score = evidence_status_score[status]
            if status == "PASS":
                item["status"] = "EVIDENCE"
                if item.get("score") is None:
                    item["score"] = evidence_score
                item["reason"] = evidence.get("observation") or item.get("reason")
                item["basis"] = ["automatic_evidence", item.get("key")]
            elif item.get("status") == "UNKNOWN":
                item["status"] = "INFERENCE"
                item["score"] = evidence_score
                item["reason"] = evidence.get("observation") or item.get("reason")
                item["basis"] = ["automatic_evidence", item.get("key")]

        known = [item for item in dimensions if item["status"] != "UNKNOWN"]
        evidence = [item for item in dimensions if item["status"] == "EVIDENCE"]
        inference = [item for item in dimensions if item["status"] == "INFERENCE"]
        unknown = [item for item in dimensions if item["status"] == "UNKNOWN"]

        known_scores = [item["score"] for item in known if item["score"] is not None]
        validation_score = int(round(sum(known_scores) / len(known_scores) * 10)) if known_scores else 0
        coverage_score = int(round(len(known) / len(dimensions) * 100))

        if coverage_score >= 80 and len(evidence) >= 5:
            confidence = "High"
        elif coverage_score >= 60 and len(evidence) >= 3:
            confidence = "Medium"
        else:
            confidence = "Low"

        if not unknown:
            summary = "The analysis has broad supporting coverage across the current dimensions."
        elif len(unknown) <= 2:
            summary = f"The analysis is reasonably covered, but {len(unknown)} information gap(s) remain."
        else:
            summary = f"The analysis still has {len(unknown)} important information gap(s); this does not trigger a manual validation workflow."

        return {
            "validation_score": validation_score,
            "coverage_score": coverage_score,
            "confidence": confidence,
            "known_dimensions": len(known),
            "total_dimensions": len(dimensions),
            "evidence": evidence,
            "inference": inference,
            "unknown": unknown,
            "dimensions": dimensions,
            "summary": summary,
            "automatic_evidence_count": len(automatic_evidence),
        }
