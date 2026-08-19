from __future__ import annotations

from typing import Any

from database.founder_decision_repository import FounderDecisionRepository


class FounderDecision:
    DECISIONS = ("BUILD", "VALIDATE", "WATCH", "KILL")

    def __init__(self) -> None:
        self.repository = FounderDecisionRepository()

    @staticmethod
    def _evidence_counts(evidence: dict | None) -> tuple[int, int, int]:
        evidence = evidence or {}
        return (
            int(evidence.get("passed", 0) or 0),
            int(evidence.get("failed", 0) or 0),
            int(evidence.get("partial", 0) or 0),
        )

    @classmethod
    def recommend(
        cls,
        validation: dict,
        revenue: dict,
        evidence: dict | None = None,
        existing_decision: dict | None = None,
    ) -> dict:
        passed, failed, partial = cls._evidence_counts(evidence)
        score = int(validation.get("validation_score", 0) or 0)
        coverage = int(validation.get("coverage_score", 0) or 0)
        confidence = str(validation.get("confidence") or "Low")
        pricing_known = bool(revenue.get("pricing_known"))
        target_path_known = bool(
            pricing_known and revenue.get("pricing_currency") == "EUR"
        )
        customers = revenue.get("customers_required")

        if failed >= 2 or (failed >= 1 and score < 45):
            decision = "KILL"
            rationale = "Founder evidence contains material failures that outweigh the current positive signal."
            next_action = "Document the failure and stop spending build time until new evidence materially changes the picture."
        elif (
            score >= 80
            and coverage >= 80
            and passed >= 3
            and target_path_known
            and customers is not None
            and customers <= 25
        ):
            decision = "BUILD"
            rationale = "The opportunity has strong validation coverage, multiple positive founder evidence signals and a concrete EUR path to the €500/month target."
            next_action = "Define the smallest MVP and start customer acquisition/validation in parallel."
        elif score >= 55 or coverage >= 60 or partial > 0 or pricing_known:
            decision = "VALIDATE"
            rationale = "The opportunity has enough signal to justify targeted validation, but the evidence is not yet strong enough for a build commitment."
            next_action = "Complete the highest-priority validation test and record the result."
        else:
            decision = "WATCH"
            rationale = "The available evidence is still too thin to justify active validation or a build commitment."
            next_action = "Keep monitoring the opportunity and collect stronger market evidence."

        return {
            "recommended_decision": decision,
            "current_decision": (existing_decision or {}).get("decision") if existing_decision else None,
            "effective_decision": (existing_decision or {}).get("decision") if existing_decision else decision,
            "rationale": (existing_decision or {}).get("rationale") if existing_decision else rationale,
            "next_action": (existing_decision or {}).get("next_action") if existing_decision else next_action,
            "engine_rationale": rationale,
            "validation_score": score,
            "coverage_score": coverage,
            "evidence_passed": passed,
            "evidence_failed": failed,
            "evidence_partial": partial,
            "confidence": confidence,
        }

    def save_founder_decision(self, opportunity_id: int, decision: str, rationale: str, next_action: str) -> int:
        return self.repository.save(
            opportunity_id, decision, rationale, next_action, source="founder"
        )

    def latest(self, opportunity_id: int) -> dict | None:
        return self.repository.latest(opportunity_id)

    def close(self) -> None:
        self.repository.close()
