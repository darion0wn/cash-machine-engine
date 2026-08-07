from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from database.database import Database
from .dashboard_service import DashboardService


class FeedService:

    def __init__(self):
        self.dashboard_service = DashboardService()

    def _query_all(self, sql: str, params: tuple = ()) -> list[dict]:
        db = Database()

        try:
            cursor = db.conn.cursor()
            cursor.execute(sql, params)

            rows = cursor.fetchall()
            columns = [
                description[0]
                for description in (cursor.description or [])
            ]

            return [
                dict(zip(columns, row))
                for row in rows
            ]

        finally:
            db.conn.close()

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
                pass

            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
            ):
                try:
                    return datetime.strptime(text, fmt)
                except ValueError:
                    continue

        return None

    @classmethod
    def _format_datetime(cls, value: Any) -> str:

        dt = cls._parse_datetime(value)

        if dt is None:
            return "Unknown"

        return dt.strftime("%d %b %Y %H:%M")

    @staticmethod
    def _parse_json_list(value: Any) -> list[str]:

        if value is None:
            return []

        if isinstance(value, list):
            return [
                str(item).strip()
                for item in value
                if str(item).strip()
            ]

        if isinstance(value, tuple):
            return [
                str(item).strip()
                for item in value
                if str(item).strip()
            ]

        if isinstance(value, str):

            text = value.strip()

            if not text:
                return []

            try:
                parsed = json.loads(text)
            except Exception:
                parsed = text

            if isinstance(parsed, list):
                return [
                    str(item).strip()
                    for item in parsed
                    if str(item).strip()
                ]

            if isinstance(parsed, str):

                text = parsed.strip()

                return [text] if text else []

        return []

    @staticmethod
    def _split_category(category: Any) -> list[str]:

        if not category:
            return []

        if not isinstance(category, str):
            category = str(category)

        parts = []

        for chunk in category.split("/"):

            chunk = chunk.strip()

            if not chunk:
                continue

            parts.append(chunk)

        return parts

    @staticmethod
    def _merge_topics(*topic_lists: list[str]) -> list[str]:

        merged = []
        seen = set()

        for topic_list in topic_lists:

            for topic in topic_list:

                normalized = str(topic).strip()

                if not normalized:
                    continue

                key = normalized.lower()

                if key in seen:
                    continue

                seen.add(key)
                merged.append(normalized)

        return merged

    @staticmethod
    def _primary_topic(topics: list[str], fallback: str = "Unknown") -> str:

        if topics:
            return topics[0]

        return fallback or "Unknown"

    @staticmethod
    def _snippet(*candidates: Any, limit: int = 120) -> str:

        for candidate in candidates:

            if candidate is None:
                continue

            text = str(candidate).strip()

            if not text:
                continue

            text = " ".join(text.split())

            if len(text) <= limit:
                return text

            return text[: limit - 1].rstrip() + "…"

        return "No additional context available."

    @staticmethod
    def _status_badge(value: str | None) -> str:

        mapping = {
            "BUILD": "🟢 BUILD",
            "WATCH": "🟡 WATCH",
            "SKIP": "❌ SKIP",
        }

        return mapping.get((value or "").upper(), value or "Unknown")

    def _query_bucket(self, status: str, limit: int = 6) -> list[dict]:

        rows = self._query_all(
            """
            SELECT
                a.id AS analysis_id,
                a.opportunity_id,
                o.source,
                o.title,
                o.url,
                o.topics AS opportunity_topics,
                a.topics AS analysis_topics,
                a.category,
                a.problem,
                a.next_action,
                a.biggest_risk,
                a.cash_machine_score,
                a.ranking_score,
                a.portfolio_status,
                a.build_verdict,
                a.created_at AS analysis_created_at
            FROM analyses a
            JOIN opportunities o
              ON o.id = a.opportunity_id
            WHERE a.portfolio_status = ?
              AND a.ranking_score > 0
            ORDER BY
                a.ranking_score DESC,
                a.cash_machine_score DESC,
                a.id DESC
            LIMIT ?
            """,
            (status, limit),
        )

        items = []

        for row in rows:

            opportunity_topics = self._parse_json_list(
                row.get("opportunity_topics")
            )
            analysis_topics = self._parse_json_list(
                row.get("analysis_topics")
            )
            category_topics = self._split_category(
                row.get("category")
            )

            merged_topics = self._merge_topics(
                analysis_topics,
                opportunity_topics,
                category_topics,
            )

            items.append(
                {
                    "analysis_id": row.get("analysis_id"),
                    "opportunity_id": row.get("opportunity_id"),
                    "source": row.get("source") or "",
                    "title": row.get("title") or "",
                    "url": row.get("url") or "",
                    "cash_machine_score": row.get("cash_machine_score") or 0,
                    "ranking_score": row.get("ranking_score") or 0,
                    "portfolio_status": row.get("portfolio_status") or "WATCH",
                    "build_verdict": row.get("build_verdict") or "Unknown",
                    "primary_topic": self._primary_topic(
                        merged_topics,
                        row.get("category") or "Unknown",
                    ),
                    "topics": merged_topics,
                    "analysis_created_at": self._format_datetime(
                        row.get("analysis_created_at")
                    ),
                    "snippet": self._snippet(
                        row.get("next_action"),
                        row.get("biggest_risk"),
                        row.get("problem"),
                    ),
                    "status_badge": self._status_badge(
                        row.get("portfolio_status")
                    ),
                }
            )

        return items

    def get_feed_data(self) -> dict:

        summary = self.dashboard_service.get_summary()
        hot_topics = self.dashboard_service.get_hot_topics(5)

        build_items = self._query_bucket("BUILD", 6)
        watch_items = self._query_bucket("WATCH", 6)
        skip_items = self._query_bucket("SKIP", 6)

        sections = [
            {
                "label": "BUILD",
                "tone": "build",
                "description": "High-priority opportunities that deserve builder attention.",
                "count": summary["build_count"],
                "items": build_items,
                "empty_message": "No BUILD opportunities yet.",
            },
            {
                "label": "WATCH",
                "tone": "watch",
                "description": "Promising ideas worth monitoring until the signal gets stronger.",
                "count": summary["watch_count"],
                "items": watch_items,
                "empty_message": "No WATCH opportunities yet.",
            },
            {
                "label": "SKIP",
                "tone": "skip",
                "description": "Ideas that are likely too weak or too crowded to pursue now.",
                "count": summary["skip_count"],
                "items": skip_items,
                "empty_message": "No SKIP opportunities yet.",
            },
        ]

        visible_rows = sum(
            len(section["items"])
            for section in sections
        )

        metrics = [
            {
                "label": "BUILD",
                "value": summary["build_count"],
                "hint": "High-priority opportunities",
                "tone": "build",
            },
            {
                "label": "WATCH",
                "value": summary["watch_count"],
                "hint": "Worth monitoring",
                "tone": "watch",
            },
            {
                "label": "SKIP",
                "value": summary["skip_count"],
                "hint": "Not worth building now",
                "tone": "skip",
            },
            {
                "label": "Avg Cash",
                "value": f"{summary['avg_cash_score']:.1f}",
                "hint": "AI opportunity score",
                "tone": "cash",
            },
            {
                "label": "Avg Rank",
                "value": f"{summary['avg_ranking_score']:.1f}",
                "hint": "Ranking engine average",
                "tone": "rank",
            },
            {
                "label": "Topics",
                "value": summary["topics_count"],
                "hint": "Normalized hot topics",
                "tone": "topics",
            },
        ]

        return {
            "summary": summary,
            "metrics": metrics,
            "sections": sections,
            "hot_topics": hot_topics,
            "visible_rows": visible_rows,
        }
