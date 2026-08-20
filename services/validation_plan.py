from __future__ import annotations

from typing import Any


class ValidationPlan:
    """Expose the current analysis-quality state without creating manual work.

    The AI analysis is the primary evaluation. This helper intentionally does
    not generate customer-interview, WTP, distribution, or MVP tasks that the
    founder must complete. Real-world validation can happen later, but it is
    outside the automated discovery/decision loop.
    """

    @classmethod
    def build(cls, analysis: dict[str, Any] | None) -> dict[str, Any]:
        analysis = analysis or {}
        if not analysis:
            return {
                "summary": "No completed analysis is available yet.",
                "total_steps": 0,
                "pending_steps": 0,
                "completed_steps": 0,
                "pass_steps": 0,
                "fail_steps": 0,
                "plan": [],
                "next_step": None,
            }

        validation = analysis.get("validation") or {}
        unknown = [
            item.get("label") or item.get("key")
            for item in validation.get("unknown", [])
            if item.get("key")
        ]
        coverage = validation.get("coverage_score", 0) or 0
        confidence = validation.get("confidence", "Low") or "Low"

        if unknown:
            gap_text = ", ".join(str(item) for item in unknown[:4])
            if len(unknown) > 4:
                gap_text += f" + {len(unknown) - 4} more"
            summary = (
                f"AI analysis complete. Quality coverage: {coverage}%. "
                f"Confidence: {confidence}. Information gaps: {gap_text}. "
                "No manual validation action is required by the engine."
            )
        else:
            summary = (
                f"AI analysis complete with {coverage}% information coverage "
                f"and {confidence} confidence. No manual validation action is "
                "required by the engine."
            )

        return {
            "summary": summary,
            "total_steps": 0,
            "pending_steps": 0,
            "completed_steps": 0,
            "pass_steps": 0,
            "fail_steps": 0,
            "plan": [],
            "next_step": None,
        }
