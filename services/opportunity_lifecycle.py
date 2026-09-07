from __future__ import annotations

from datetime import datetime
from typing import Any

from database.database import Database
from database.lifecycle_repository import LifecycleRepository


class OpportunityLifecycle:
    STAGES = (
        "DISCOVERED",
        "ANALYZED",
        "VALIDATING",
        "VALIDATED",
        "BUILDING",
        "LAUNCHED",
        "REVENUE_500",
        "KILLED",
    )

    LABELS = {
        "DISCOVERED": "Discovered",
        "ANALYZED": "Analyzed",
        "VALIDATING": "Validating",
        "VALIDATED": "Validated",
        "BUILDING": "Building",
        "LAUNCHED": "Launched",
        "REVENUE_500": "€500 MRR",
        "KILLED": "Killed",
    }

    TERMINAL = {"REVENUE_500", "KILLED"}

    def __init__(self, db: Database | None = None) -> None:
        self.repository = LifecycleRepository(db=db)

    @classmethod
    def infer_default_stage(cls, analysis: dict | None) -> str:
        if not analysis:
            return "DISCOVERED"
        decision = str(
            (analysis.get("founder_decision") or {}).get("effective_decision")
            or ""
        ).upper()
        if decision == "KILL":
            return "KILLED"
        if decision == "BUILD":
            return "BUILDING"
        if decision == "VALIDATE":
            return "VALIDATING"
        return "ANALYZED"

    @classmethod
    def _next_actions(cls, stage: str) -> list[str]:
        return {
            "DISCOVERED": ["Run the analysis and decide whether the signal deserves attention."],
            "ANALYZED": ["Continue monitoring the opportunity through new discovery and trend signals."],
            "VALIDATING": ["The engine is tracking the remaining information gaps automatically."],
            "VALIDATED": ["Define the smallest MVP and lock the first acquisition channel."],
            "BUILDING": ["Ship the smallest useful version and start acquiring first customers."],
            "LAUNCHED": ["Measure activation, retention and revenue against the €500/month target."],
            "REVENUE_500": ["Protect the revenue base and decide whether to scale beyond €500/month."],
            "KILLED": ["Archive the decision and reuse the lessons for the next opportunity."],
        }.get(stage, [])

    @staticmethod
    def _format_datetime(value: Any) -> str:
        if value is None:
            return "Unknown"
        if isinstance(value, datetime):
            return value.strftime("%d %b %Y %H:%M")
        text = str(value).strip()
        try:
            dt = datetime.fromisoformat(text)
            return dt.strftime("%d %b %Y %H:%M")
        except ValueError:
            return text

    def get(self, opportunity_id: int, analysis: dict | None = None) -> dict:
        current = self.repository.current(opportunity_id)
        if current is None:
            stage = self.infer_default_stage(analysis)
            current = {
                "id": None,
                "opportunity_id": opportunity_id,
                "stage": stage,
                "reason": "Inferred from the current analysis and founder decision.",
                "source": "engine",
                "changed_at": None,
            }
        history = self.repository.history(opportunity_id)
        return {
            "current_stage": current["stage"],
            "current_label": self.LABELS.get(current["stage"], current["stage"]),
            "current_reason": current.get("reason") or "",
            "current_changed_at": self._format_datetime(current.get("changed_at")),
            "current_source": current.get("source") or "engine",
            "history": [
                {
                    **item,
                    "label": self.LABELS.get(item["stage"], item["stage"]),
                    "changed_at_label": self._format_datetime(item.get("changed_at")),
                }
                for item in history
            ],
            "stages": [
                {
                    "key": stage,
                    "label": self.LABELS[stage],
                    "active": stage == current["stage"],
                    "terminal": stage in self.TERMINAL,
                }
                for stage in self.STAGES
            ],
            "next_actions": self._next_actions(current["stage"]),
            "terminal": current["stage"] in self.TERMINAL,
        }

    def transition(
        self,
        opportunity_id: int,
        stage: str,
        reason: str,
        source: str = "founder",
    ) -> int:
        return self.repository.save(
            opportunity_id,
            stage=stage,
            reason=reason,
            source=source,
        )

    @classmethod
    def stage_for_decision(cls, decision: str) -> str:
        return {
            "BUILD": "BUILDING",
            "VALIDATE": "VALIDATING",
            "WATCH": "ANALYZED",
            "KILL": "KILLED",
        }.get(str(decision or "WATCH").upper(), "ANALYZED")

    def sync_from_decision(self, opportunity_id: int, decision: str, validation: dict | None = None) -> int:
        stage = self.stage_for_decision(decision)
        validation = validation or {}
        reason = (
            f"Automatic lifecycle stage derived from engine decision {str(decision or 'WATCH').upper()} "
            f"with validation score {int(validation.get('validation_score', 0) or 0)}/100 "
            f"and {int(validation.get('coverage_score', 0) or 0)}% coverage."
        )
        return self.repository.save(
            opportunity_id,
            stage=stage,
            reason=reason,
            source="engine",
        )

    def close(self) -> None:
        self.repository.close()
