from __future__ import annotations

from typing import Any


class ValidationPlan:
    """Build a deterministic, evidence-first validation plan for an opportunity.

    The plan is intentionally stateless. Step 18.4 will persist the execution
    results; this layer only defines what should be tested and how success/failure
    should be judged.
    """

    @staticmethod
    def _known(value: Any) -> bool:
        if value is None:
            return False
        text = str(value).strip().lower()
        return text not in {"", "unknown", "n/a", "na", "none", "not available"}

    @staticmethod
    def _unknown_keys(validation: dict[str, Any]) -> set[str]:
        return {
            item.get("key")
            for item in validation.get("unknown", [])
            if item.get("key")
        }

    @classmethod
    def build(cls, analysis: dict[str, Any] | None) -> dict[str, Any]:
        analysis = analysis or {}
        validation = analysis.get("validation") or {}
        unknown = cls._unknown_keys(validation)

        plan: list[dict[str, Any]] = []

        def add(
            key: str,
            title: str,
            goal: str,
            evidence: str,
            pass_criteria: str,
            fail_criteria: str,
            priority: str,
            basis: list[str],
        ) -> None:
            plan.append(
                {
                    "key": key,
                    "title": title,
                    "goal": goal,
                    "evidence_to_collect": evidence,
                    "pass_criteria": pass_criteria,
                    "fail_criteria": fail_criteria,
                    "priority": priority,
                    "basis": basis,
                    "status": "PENDING",
                }
            )

        add(
            "customer_interviews",
            "Customer interviews",
            "Confirm that the target customer experiences the stated problem frequently enough to care.",
            "5 conversations with people who match the stated ideal customer profile; record current workflow, frequency, severity and existing workaround.",
            "At least 3 of 5 conversations confirm the problem is real, recurring and materially painful.",
            "Fewer than 2 of 5 confirm a meaningful recurring problem, or the stated customer cannot be reached.",
            "HIGH" if "problem_severity" in unknown or "target_customer_clarity" in unknown else "MEDIUM",
            ["problem_severity", "target_customer_clarity"],
        )

        add(
            "willingness_to_pay",
            "Pricing / willingness-to-pay test",
            "Verify that the target customer would exchange money for the proposed outcome.",
            "Ask qualified prospects for a concrete reaction to the proposed pricing and, where possible, request a paid pilot, deposit or explicit buying commitment.",
            "At least 2 qualified prospects give a concrete positive buying signal at or near the proposed price.",
            "Prospects reject the price, consistently prefer a free workaround, or will not commit to a next commercial step.",
            "HIGH" if "willingness_to_pay" in unknown else "MEDIUM",
            ["willingness_to_pay"],
        )

        add(
            "current_solution",
            "Current-solution validation",
            "Understand what customers use today and why the current solution is insufficient.",
            "Capture the incumbent tool/workflow, switching trigger, biggest complaint and what customers already spend.",
            "At least 3 target customers identify a recurring gap that the proposed solution addresses better than their current workaround.",
            "Customers are satisfied with the current solution or cannot articulate a meaningful gap.",
            "HIGH" if "competition" in unknown else "MEDIUM",
            ["competition", "problem_severity"],
        )

        add(
            "distribution_test",
            "Distribution test",
            "Verify that the first customers can be reached through a realistic acquisition channel.",
            "Pick one concrete channel and run a small test: targeted outreach, community post, landing-page traffic, marketplace listing or direct demos.",
            "The selected channel produces at least 3 qualified conversations, signups or demo requests from the target customer.",
            "The channel produces no qualified signal after a focused test or reaches the wrong audience.",
            "HIGH" if "distribution" in unknown else "MEDIUM",
            ["distribution"],
        )

        add(
            "mvp_feasibility",
            "MVP feasibility test",
            "Reduce technical uncertainty before committing to a full build.",
            "Build the smallest technical spike necessary to prove the riskiest integration, data dependency or workflow.",
            "The riskiest technical assumption works within the planned MVP constraints and effort.",
            "A core technical assumption fails or requires materially more complexity than the proposed MVP allows.",
            "HIGH" if "technical_complexity" in unknown or "time_to_mvp" in unknown else "MEDIUM",
            ["technical_complexity", "time_to_mvp"],
        )

        # Keep the most relevant tests first while retaining a consistent core set.
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        plan.sort(key=lambda item: (priority_order.get(item["priority"], 9), item["title"]))

        high_count = sum(item["priority"] == "HIGH" for item in plan)
        if not plan:
            summary = "No validation plan can be generated until a completed opportunity analysis is available."
        elif high_count:
            summary = (
                f"{high_count} high-priority validation test(s) should be completed before a build commitment."
            )
        else:
            summary = "Core validation checks remain important before committing build time."

        return {
            "summary": summary,
            "total_steps": len(plan),
            "pending_steps": len(plan),
            "completed_steps": 0,
            "pass_steps": 0,
            "fail_steps": 0,
            "plan": plan,
            "next_step": plan[0]["title"] if plan else None,
        }
