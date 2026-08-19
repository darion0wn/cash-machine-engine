from __future__ import annotations

from datetime import datetime
from typing import Any

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

    def __init__(self) -> None:
        self.repository = LifecycleRepository()

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
            "ANALYZED": ["Review validation gaps and choose the highest-priority test."],
            "VALIDATING": ["Collect real customer, pricing or distribution evidence."],
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

    def close(self) -> None:
        self.repository.close()
