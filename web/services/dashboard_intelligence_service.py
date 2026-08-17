from __future__ import annotations

from datetime import datetime
from typing import Any

from database.database import Database
from services.decision_engine import DecisionEngine


class DashboardIntelligenceService:
    """Builds decision-oriented signals for the founder dashboard."""

    def _query_all(
        self,
        sql: str,
        params: tuple = (),
    ) -> list[dict[str, Any]]:
        db = Database()

        try:
            cursor = db.conn.cursor()
            cursor.execute(sql, params)

            rows = cursor.fetchall()
            columns = [
                description[0]
                for description in (cursor.description or [])
            ]

            return [dict(zip(columns, row)) for row in rows]

        finally:
            db.conn.close()

    def _query_one(
        self,
        sql: str,
        params: tuple = (),
    ) -> dict[str, Any] | None:
        rows = self._query_all(sql, params)
        return rows[0] if rows else None

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None

            try:
                return datetime.fromisoformat(text)
            except ValueError:
                return None

        return None

    @staticmethod
    def _format_datetime(value: Any) -> str:
        dt = DashboardIntelligenceService._parse_datetime(value)

        if dt is None:
            return "Not available"

        return dt.strftime("%d %b %Y %H:%M")

    @staticmethod
    def _safe_int(value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    def _get_completed_runs(self) -> list[dict[str, Any]]:
        return self._query_all(
            """
            SELECT
                id,
                started_at,
                finished_at,
                status,
                return_code
            FROM refresh_runs
            WHERE status = 'completed'
            ORDER BY id DESC
            LIMIT 2
            """
        )

    def _get_window(
        self,
        latest_run: dict[str, Any] | None,
        previous_run: dict[str, Any] | None,
    ) -> tuple[str | None, str | None]:
        if latest_run is None:
            return None, None

        start = (
            previous_run.get("finished_at")
            if previous_run
            else latest_run.get("started_at")
        )
        end = latest_run.get("finished_at")

        return start, end

    def _get_new_counts(
        self,
        start: str | None,
        end: str | None,
    ) -> dict[str, int]:
        if not start or not end:
            return {
                "new_analyses": 0,
                "new_build": 0,
                "new_watch": 0,
                "new_skip": 0,
            }

        row = self._query_one(
            """
            SELECT
                COUNT(*) AS new_analyses,
                SUM(
                    CASE
                        WHEN portfolio_status = 'BUILD' THEN 1
                        ELSE 0
                    END
                ) AS new_build,
                SUM(
                    CASE
                        WHEN portfolio_status = 'WATCH' THEN 1
                        ELSE 0
                    END
                ) AS new_watch,
                SUM(
                    CASE
                        WHEN portfolio_status = 'SKIP' THEN 1
                        ELSE 0
                    END
                ) AS new_skip
            FROM analyses
            WHERE created_at > ?
              AND created_at <= ?
            """,
            (start, end),
        ) or {}

        return {
            "new_analyses": self._safe_int(row.get("new_analyses")),
            "new_build": self._safe_int(row.get("new_build")),
            "new_watch": self._safe_int(row.get("new_watch")),
            "new_skip": self._safe_int(row.get("new_skip")),
        }

    def _get_focus_opportunity(
        self,
        start: str | None,
        end: str | None,
    ) -> dict[str, Any] | None:
        params: list[Any] = []
        where = ["a.ranking_score > 0"]

        if start and end:
            where.append("a.created_at > ?")
            params.append(start)

            where.append("a.created_at <= ?")
            params.append(end)

        query = f"""
            SELECT
                a.opportunity_id,
                o.title,
                o.source,
                a.cash_machine_score,
                a.ranking_score,
                a.build_verdict,
                a.portfolio_status,
                a.next_action,
                a.problem_score,
                a.market_score,
                a.business_score,
                a.implementation_difficulty,
                a.competition_level,
                a.monetization_difficulty,
                a.distribution_score,
                a.pricing_strategy
            FROM analyses a
            JOIN opportunities o
              ON o.id = a.opportunity_id
            WHERE {' AND '.join(where)}
            ORDER BY
                a.ranking_score DESC,
                a.cash_machine_score DESC,
                a.id DESC
            LIMIT 1
        """

        row = self._query_one(query, tuple(params))

        if row is None and start and end:
            return self._get_focus_opportunity(None, None)

        if row is None:
            return None

        focus = {
            "opportunity_id": self._safe_int(row.get("opportunity_id")),
            "title": row.get("title") or "Untitled opportunity",
            "source": row.get("source") or "Unknown source",
            "cash_machine_score": self._safe_int(
                row.get("cash_machine_score")
            ),
            "ranking_score": self._safe_int(row.get("ranking_score")),
            "build_verdict": row.get("build_verdict") or "WATCH",
            "portfolio_status": row.get("portfolio_status") or "WATCH",
            "next_action": (
                row.get("next_action")
                or "Open the opportunity and validate the signal."
            ),
            "problem_score": self._safe_int(row.get("problem_score")),
            "market_score": self._safe_int(row.get("market_score")),
            "business_score": self._safe_int(row.get("business_score")),
            "implementation_difficulty": self._safe_int(row.get("implementation_difficulty")),
            "competition_level": self._safe_int(row.get("competition_level")),
            "monetization_difficulty": self._safe_int(row.get("monetization_difficulty")),
            "distribution_score": self._safe_int(row.get("distribution_score")),
            "pricing_strategy": row.get("pricing_strategy") or "",
        }
        focus["decision"] = DecisionEngine.evaluate(focus)
        return focus


    def _get_decision_mix(self) -> dict[str, Any]:
        row = self._query_one(
            """
            SELECT
                COALESCE(SUM(CASE WHEN portfolio_status = 'BUILD' THEN 1 ELSE 0 END), 0) AS build,
                COALESCE(SUM(CASE WHEN portfolio_status = 'WATCH' THEN 1 ELSE 0 END), 0) AS watch,
                COALESCE(SUM(CASE WHEN portfolio_status = 'SKIP' THEN 1 ELSE 0 END), 0) AS skip
            FROM analyses
            """
        ) or {}

        return {
            "labels": ["BUILD", "WATCH", "SKIP"],
            "values": [
                self._safe_int(row.get("build")),
                self._safe_int(row.get("watch")),
                self._safe_int(row.get("skip")),
            ],
        }

    def _get_cash_distribution(self) -> dict[str, Any]:
        rows = self._query_all(
            """
            SELECT
                CASE
                    WHEN cash_machine_score < 20 THEN '0–19'
                    WHEN cash_machine_score < 40 THEN '20–39'
                    WHEN cash_machine_score < 60 THEN '40–59'
                    WHEN cash_machine_score < 80 THEN '60–79'
                    ELSE '80–100'
                END AS bucket,
                COUNT(*) AS count
            FROM analyses
            GROUP BY
                CASE
                    WHEN cash_machine_score < 20 THEN '0–19'
                    WHEN cash_machine_score < 40 THEN '20–39'
                    WHEN cash_machine_score < 60 THEN '40–59'
                    WHEN cash_machine_score < 80 THEN '60–79'
                    ELSE '80–100'
                END
            """
        )

        order = ["0–19", "20–39", "40–59", "60–79", "80–100"]
        counts = {row.get("bucket"): self._safe_int(row.get("count")) for row in rows}

        return {
            "labels": order,
            "values": [counts.get(bucket, 0) for bucket in order],
        }

    def _get_recent_activity(self) -> dict[str, Any]:
        rows = self._query_all(
            """
            SELECT
                DATE(created_at) AS activity_date,
                COUNT(*) AS count
            FROM analyses
            WHERE created_at >= DATE('now', '-6 day')
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at)
            """
        )

        counts = {
            str(row.get("activity_date")): self._safe_int(row.get("count"))
            for row in rows
            if row.get("activity_date")
        }

        labels = []
        values = []

        from datetime import timedelta

        today = datetime.utcnow().date()

        for offset in range(6, -1, -1):
            current = today - timedelta(days=offset)
            key = current.isoformat()
            labels.append(current.strftime("%d %b"))
            values.append(counts.get(key, 0))

        return {
            "labels": labels,
            "values": values,
        }

    def _get_trend_momentum(
        self,
        hot_topics: list[dict[str, Any]] | None,
        limit: int = 8,
    ) -> dict[str, Any]:
        topics = (hot_topics or [])[:limit]

        return {
            "labels": [str(item.get("topic") or "Unknown") for item in topics],
            "values": [
                round(float(item.get("trend_score") or 0), 1)
                for item in topics
            ],
        }

    def get_chart_data(
        self,
        hot_topics: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            "decision_mix": self._get_decision_mix(),
            "cash_distribution": self._get_cash_distribution(),
            "trend_momentum": self._get_trend_momentum(hot_topics),
            "recent_activity": self._get_recent_activity(),
        }

    @staticmethod
    def _build_founder_signal(
        focus: dict[str, Any] | None,
        new_counts: dict[str, int],
        top_topic: dict[str, Any] | None,
    ) -> str:
        if focus:
            title = focus["title"]
            rank = focus["ranking_score"]
            verdict = focus["portfolio_status"]

            if new_counts["new_analyses"] > 0:
                if top_topic:
                    return (
                        f"{new_counts['new_analyses']} new analyses arrived. "
                        f"{title} is the strongest current signal "
                        f"({verdict}, rank {rank}), while "
                        f"{top_topic.get('topic', 'the leading topic')} "
                        "is the top market theme."
                    )

                return (
                    f"{new_counts['new_analyses']} new analyses arrived. "
                    f"{title} is the strongest current signal "
                    f"({verdict}, rank {rank})."
                )

            return (
                f"No new analysis window is available yet. "
                f"The strongest current signal is {title} "
                f"({verdict}, rank {rank})."
            )

        if top_topic:
            return (
                f"No ranked opportunity is available yet. "
                f"{top_topic.get('topic', 'A market topic')} is the "
                "strongest detected theme."
            )

        return (
            "No founder signal is available yet. "
            "Run the crawler to populate the workspace."
        )

    def get_intelligence(
        self,
        hot_topics: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        runs = self._get_completed_runs()

        latest_run = runs[0] if runs else None
        previous_run = runs[1] if len(runs) > 1 else None

        start, end = self._get_window(
            latest_run,
            previous_run,
        )

        new_counts = self._get_new_counts(start, end)

        focus = self._get_focus_opportunity(start, end)

        if not hot_topics:
            top_topic = None
        else:
            top_topic = hot_topics[0]

        return {
            "last_refresh": self._format_datetime(
                latest_run.get("finished_at")
                if latest_run
                else None
            ),
            "previous_refresh": self._format_datetime(
                previous_run.get("finished_at")
                if previous_run
                else None
            ),
            "new_analyses": new_counts["new_analyses"],
            "new_build": new_counts["new_build"],
            "new_watch": new_counts["new_watch"],
            "new_skip": new_counts["new_skip"],
            "focus_opportunity": focus,
            "top_topic": top_topic,
            "founder_signal": self._build_founder_signal(
                focus,
                new_counts,
                top_topic,
            ),
            "charts": self.get_chart_data(hot_topics),
        }
