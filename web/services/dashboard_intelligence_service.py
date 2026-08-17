from __future__ import annotations

from datetime import datetime
from typing import Any

from database.database import Database


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
                a.next_action
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

        return {
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
        }
