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
        decision_context: dict | None = None,
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
            "SKIP": "WATCH",
            "KILL": "KILL",
            "VALIDATE": "VALIDATE",
        }
        decision = decision_map.get(ai_verdict, "WATCH")
        decision_context = decision_context or {}

        score = int(validation.get("validation_score", 0) or 0)
        evidence_passed, evidence_failed, evidence_partial = cls._evidence_counts(evidence)
        coverage = int(validation.get("coverage_score", 0) or 0)
        confidence = str(validation.get("confidence") or "Low")

        if existing_decision and existing_decision.get("source") == "founder":
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
            "evidence_passed": evidence.get("automatic_counts", {}).get("PASS", evidence_passed) if evidence else evidence_passed,
            "evidence_failed": evidence.get("automatic_counts", {}).get("FAIL", evidence_failed) if evidence else evidence_failed,
            "evidence_partial": evidence.get("automatic_counts", {}).get("PARTIAL", evidence_partial) if evidence else evidence_partial,
            "decision_score": int(decision_context.get("decision_score", 0) or 0),
            "decision_label": decision_context.get("decision_label") or "Unknown",
            "confidence": confidence,
        }

    def save_founder_decision(self, opportunity_id: int, decision: str, rationale: str, next_action: str) -> int:
        return self.repository.save(
            opportunity_id, decision, rationale, next_action, source="founder"
        )

    def sync_automatic_decision(self, opportunity_id: int, recommendation: dict) -> dict:
        """Persist the engine decision without overwriting a founder override."""
        latest = self.repository.latest(opportunity_id)
        if latest and latest.get("source") == "founder":
            return latest

        decision = recommendation.get("effective_decision") or recommendation.get("recommended_decision") or "WATCH"
        rationale = recommendation.get("engine_rationale") or recommendation.get("rationale") or ""
        next_action = recommendation.get("next_action") or ""

        if latest and latest.get("source") == "engine" and (
            latest.get("decision") == decision
            and latest.get("rationale") == rationale
            and latest.get("next_action") == next_action
        ):
            return latest

        return self.repository.save_engine(
            opportunity_id,
            decision,
            rationale,
            next_action,
        )

    def latest(self, opportunity_id: int) -> dict | None:
        return self.repository.latest(opportunity_id)

    def close(self) -> None:
        self.repository.close()
