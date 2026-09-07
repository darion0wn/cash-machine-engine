from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from database.database import Database
from services.opportunity_lifecycle import OpportunityLifecycle
from web.services.dashboard_service import DashboardService


class WeeklyBriefService:
    DAYS = 7

    def _query_all(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        db = Database()
        try:
            cursor = db.conn.execute(sql, params)
            columns = [d[0] for d in cursor.description or []]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            db.conn.close()

    @classmethod
    def _window_start(cls) -> str:
        return (datetime.now() - timedelta(days=cls.DAYS)).strftime("%Y-%m-%d %H:%M:%S")

    def _weekly_rows(self) -> list[dict[str, Any]]:
        return self._query_all(
            """
            SELECT
                a.id AS analysis_id,
                a.opportunity_id,
                o.title,
                o.source,
                a.cash_machine_score,
                a.ranking_score,
                a.build_verdict,
                a.portfolio_status,
                a.created_at
            FROM analyses a
            JOIN opportunities o ON o.id = a.opportunity_id
            WHERE a.created_at >= ?
            ORDER BY a.ranking_score DESC, a.cash_machine_score DESC, a.id DESC
            """,
            (self._window_start(),),
        )

    def build(self) -> dict[str, Any]:
        rows = self._weekly_rows()
        build = sum(1 for row in rows if (row.get("build_verdict") or row.get("portfolio_status")) == "BUILD")
        watch = sum(1 for row in rows if (row.get("build_verdict") or row.get("portfolio_status")) == "WATCH")
        skip = sum(1 for row in rows if (row.get("build_verdict") or row.get("portfolio_status")) == "SKIP")

        dashboard = DashboardService()
        lifecycle = OpportunityLifecycle()
        try:
            top: list[dict[str, Any]] = []
            for row in rows[:8]:
                detail = dashboard.get_opportunity_detail(int(row["opportunity_id"]))
                if not detail or not detail.get("analysis"):
                    continue
                analysis = detail["analysis"]
                decision = analysis.get("founder_decision") or {}
                validation = analysis.get("validation") or {}
                revenue = analysis.get("revenue_simulation") or {}
                lifecycle_data = analysis.get("lifecycle") or lifecycle.get(
                    int(row["opportunity_id"]), analysis
                )
                top.append(
                    {
                        "opportunity_id": int(row["opportunity_id"]),
                        "title": row["title"],
                        "source": row["source"],
                        "cash_score": int(row.get("cash_machine_score") or 0),
                        "ranking_score": int(row.get("ranking_score") or 0),
                        "validation_score": int(validation.get("validation_score") or 0),
                        "coverage_score": int(validation.get("coverage_score") or 0),
                        "decision": decision.get("effective_decision") or decision.get("recommended_decision") or "WATCH",
                        "lifecycle_stage": lifecycle_data.get("current_label") or "Analyzed",
                        "next_action": decision.get("next_action") or analysis.get("next_action") or "Review the validation plan.",
                        "target_path": revenue.get("mathematical_path") or "€500/month path not yet quantifiable.",
                    }
                )
        finally:
            dashboard = None
            lifecycle.close()

        top.sort(
            key=lambda item: (
                1 if item["decision"] == "BUILD" else 0,
                item["validation_score"],
                item["coverage_score"],
                item["cash_score"],
                item["ranking_score"],
            ),
            reverse=True,
        )
        top = top[:3]

        return {
            "generated_at": datetime.now().strftime("%d %b %Y %H:%M"),
            "window_label": "Last 7 days",
            "metrics": {
                "analyses": len(rows),
                "build": build,
                "watch": watch,
                "skip": skip,
                "validated_or_build": sum(
                    1 for item in top if item["decision"] in {"BUILD", "VALIDATED"}
                ),
            },
            "top_opportunities": top,
            "recommendation": self._recommendation(top, len(rows)),
        }

    @staticmethod
    def _recommendation(top: list[dict[str, Any]], total: int) -> str:
        if not total:
            return "No new analyses were created in the last 7 days. Keep the scheduler and refresh pipeline running before making a build decision."
        if not top:
            return "The current week does not contain enough evidence to recommend a focused build. Continue validation."
        first = top[0]
        return (
            f"Focus first on {first['title']}. It currently combines the strongest validation signal in the weekly window "
            f"with a {first['decision']} recommendation. Next: {first['next_action']}"
        )
