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
        analysis: dict | None = None,
    ) -> dict:
        """Return the current automatic decision without manual evidence gates.

        The AI analysis/ranking remains the primary decision source. Validation
        and revenue are supporting context only; evidence records are optional
        founder notes and never required to promote/demote an opportunity.
        """
        analysis = analysis or {}
        ai_verdict = str(
            analysis.get("portfolio_status")
            or analysis.get("build_verdict")
            or "WATCH"
        ).upper()

        decision_map = {
            "BUILD": "BUILD",
            "WATCH": "WATCH",
            "SKIP": "KILL",
            "KILL": "KILL",
            "VALIDATE": "VALIDATE",
        }
        decision = decision_map.get(ai_verdict, "WATCH")

        score = int(validation.get("validation_score", 0) or 0)
        coverage = int(validation.get("coverage_score", 0) or 0)
        confidence = str(validation.get("confidence") or "Low")

        if existing_decision:
            effective_decision = existing_decision.get("decision")
            rationale = existing_decision.get("rationale") or ""
            next_action = existing_decision.get("next_action") or ""
        else:
            effective_decision = decision
            rationale = (
                f"Automatic decision derived from the existing AI/ranking verdict: "
                f"{ai_verdict}. Validation quality is informational "
                f"({coverage}% coverage, {confidence} confidence) and does not "
                "create a manual validation gate."
            )
            next_action = (
                analysis.get("next_action")
                or "Continue collecting market signals through the normal discovery and trend pipeline."
            )

        return {
            "recommended_decision": decision,
            "current_decision": (
                existing_decision.get("decision") if existing_decision else None
            ),
            "effective_decision": effective_decision,
            "rationale": rationale,
            "next_action": next_action,
            "engine_rationale": (
                f"AI verdict is {ai_verdict}; validation is informational and "
                "evidence tracking is optional."
            ),
            "validation_score": score,
            "coverage_score": coverage,
            "evidence_passed": 0,
            "evidence_failed": 0,
            "evidence_partial": 0,
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
