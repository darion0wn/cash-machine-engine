from __future__ import annotations

from web.services.dashboard_service import DashboardService
from services.evidence_tracker import EvidenceTracker
from services.founder_decision import FounderDecision


class ComparisonService:

    def __init__(self) -> None:
        self.dashboard = DashboardService()
        self.evidence = EvidenceTracker()
        self.decision = FounderDecision()

    @staticmethod
    def _normalize_ids(ids) -> list[int]:
        result = []
        seen = set()
        for value in ids:
            try:
                item = int(value)
            except (TypeError, ValueError):
                continue
            if item > 0 and item not in seen:
                seen.add(item)
                result.append(item)
        return result[:3]

    def get_comparison(self, ids: list[int]) -> dict:
        ids = self._normalize_ids(ids)
        opportunities = []
        for opportunity_id in ids:
            detail = self.dashboard.get_opportunity_detail(opportunity_id)
            if not detail or not detail.get("analysis"):
                continue
            analysis = detail["analysis"]
            evidence = self.evidence.get(opportunity_id)
            validation = analysis.get("validation") or {}
            effective_validation = self.evidence.apply_to_validation(validation, evidence.get("automatic_latest_by_key") or {})
            decision = self.decision.recommend(
                effective_validation,
                analysis.get("revenue_simulation") or {},
                evidence,
                self.decision.latest(opportunity_id),
                analysis=analysis,
                decision_context=analysis.get("decision") or {},
            )
            opportunities.append({
                "opportunity": detail["opportunity"],
                "analysis": analysis,
                "validation": effective_validation,
                "evidence": evidence,
                "decision": decision,
            })

        rankings = sorted(
            opportunities,
            key=lambda item: (
                item["validation"]["validation_score"],
                item["analysis"].get("ranking_score", 0),
                item["analysis"].get("cash_machine_score", 0),
            ),
            reverse=True,
        )

        return {
            "selected_ids": ids,
            "opportunities": opportunities,
            "ranking": [item["opportunity"]["id"] for item in rankings],
            "winner_id": rankings[0]["opportunity"]["id"] if rankings else None,
        }

    def close(self) -> None:
        self.evidence.close()
        self.decision.close()
