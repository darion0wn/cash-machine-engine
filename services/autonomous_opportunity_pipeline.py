from __future__ import annotations

from dataclasses import asdict
from typing import Any

from services.automatic_evidence_collector import AutomaticEvidenceCollector
from services.decision_engine import DecisionEngine
from services.founder_decision import FounderDecision
from services.opportunity_lifecycle import OpportunityLifecycle
from services.revenue_simulator import RevenueSimulator
from services.validation_framework import OpportunityValidationFramework
from services.evidence_tracker import EvidenceTracker
from services.telegram_alert_service import TelegramAlertService


class AutonomousOpportunityPipeline:
    """Close the automatic analysis → evidence → decision → lifecycle loop."""

    @staticmethod
    def _analysis_dict(analysis: Any) -> dict[str, Any]:
        if isinstance(analysis, dict):
            return dict(analysis)

        data = asdict(analysis)
        recommendation = data.get("investment_recommendation")
        if hasattr(recommendation, "value"):
            data["investment_recommendation"] = recommendation.value
        return data

    @staticmethod
    def process(opportunity: Any, analysis: Any, notify: bool = True) -> dict[str, Any]:
        analysis_data = AutonomousOpportunityPipeline._analysis_dict(analysis)

        validation = OpportunityValidationFramework.evaluate(analysis_data)

        collector = AutomaticEvidenceCollector()
        tracker = EvidenceTracker()
        founder_decision = FounderDecision()
        lifecycle = OpportunityLifecycle()

        # Reuse the database already opened by FounderDecision for Telegram.
        # This avoids creating another Database() instance that reruns schema
        # initialization and can block on PostgreSQL DDL locks.
        telegram = None
        if notify:
            from database.alert_repository import AlertRepository

            telegram = TelegramAlertService(
                repository=AlertRepository(
                    db=founder_decision.repository.db,
                )
            )

        try:
            signals = collector.collect(opportunity, analysis_data)
            collector.persist(int(opportunity.id), signals)

            evidence = tracker.get(int(opportunity.id))
            automatic_latest = evidence.get("automatic_latest_by_key") or {}

            validation = OpportunityValidationFramework.evaluate(
                analysis_data,
                automatic_evidence=automatic_latest,
            )

            revenue = RevenueSimulator.simulate(analysis_data)
            decision_context = DecisionEngine.evaluate(analysis_data)
            existing = founder_decision.latest(int(opportunity.id))

            decision = FounderDecision.recommend(
                validation,
                revenue,
                evidence,
                existing,
                analysis=analysis_data,
                decision_context=decision_context,
            )

            effective_decision = decision["effective_decision"]
            founder_decision.sync_automatic_decision(
                int(opportunity.id),
                decision,
            )

            lifecycle.sync_from_decision(
                int(opportunity.id),
                effective_decision,
                validation,
            )

            lifecycle_data = lifecycle.get(
                int(opportunity.id),
                {**analysis_data, "founder_decision": decision},
            )

            alert = {"sent": False, "reason": "notifications_disabled"}
            if telegram is not None:
                alert = telegram.notify(
                    opportunity,
                    analysis_data,
                    validation,
                    decision,
                    lifecycle_data,
                    previous_decision=existing,
                )

            return {
                "validation": validation,
                "evidence_tracking": evidence,
                "decision": decision,
                "decision_context": decision_context,
                "lifecycle": lifecycle_data,
                "telegram_alert": alert,
            }
        finally:
            collector.close()
            tracker.close()
            founder_decision.close()
            lifecycle.close()
            if telegram is not None:
                telegram.close()

