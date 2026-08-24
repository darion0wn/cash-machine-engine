from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

from database.database import Database
from services.topic_normalizer import TopicNormalizer
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

    FILTER_DEFAULTS = {
        "status": "ALL",
        "source": "ALL",
        "topic": "ALL",
        "min_cash": "",
        "max_rank": "",
        "date_from": "",
        "date_to": "",
        "sort": "ranking_desc",
    }

    SORT_OPTIONS = {
        "ranking_desc": "Ranking ↓",
        "ranking_asc": "Ranking ↑",
        "cash_desc": "Cash Score ↓",
        "cash_asc": "Cash Score ↑",
        "trend_desc": "Trend ↓",
        "trend_asc": "Trend ↑",
        "newest": "Newest first",
        "oldest": "Oldest first",
    }

    def _normalize_filters(self, filters: dict | None) -> dict:
        values = dict(self.FILTER_DEFAULTS)

        if filters:
            for key in values:
                value = filters.get(key)
                if value is not None:
                    values[key] = str(value).strip()

        if values["status"] not in {"ALL", "BUILD", "WATCH", "SKIP"}:
            values["status"] = "ALL"

        if values["source"] == "":
            values["source"] = "ALL"

        if values["topic"] == "":
            values["topic"] = "ALL"

        if values["sort"] not in self.SORT_OPTIONS:
            values["sort"] = self.FILTER_DEFAULTS["sort"]

        for key in ("min_cash", "max_rank"):
            try:
                number = int(values[key]) if values[key] else None
            except (TypeError, ValueError):
                number = None

            if number is not None:
                values[key] = str(max(0, min(100, number)))
            else:
                values[key] = ""

        for key in ("date_from", "date_to"):
            value = values[key]
            if value:
                try:
                    datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    values[key] = ""

        return values

    @staticmethod
    def _order_by(sort: str) -> str:
        return {
            "ranking_desc": "a.ranking_score DESC, a.cash_machine_score DESC, a.id DESC",
            "ranking_asc": "a.ranking_score ASC, a.cash_machine_score DESC, a.id DESC",
            "cash_desc": "a.cash_machine_score DESC, a.ranking_score DESC, a.id DESC",
            "cash_asc": "a.cash_machine_score ASC, a.ranking_score ASC, a.id DESC",
            "trend_desc": "a.trend_score DESC, a.ranking_score DESC, a.id DESC",
            "trend_asc": "a.trend_score ASC, a.ranking_score ASC, a.id DESC",
            "newest": "a.created_at DESC, a.id DESC",
            "oldest": "a.created_at ASC, a.id ASC",
        }.get(sort, "a.ranking_score DESC, a.cash_machine_score DESC, a.id DESC")

    def _filter_clauses(
        self,
        filters: dict,
        status: str | None = None,
    ) -> tuple[list[str], list]:
        clauses = ["a.ranking_score > 0"]
        params: list = []

        effective_status = status if status else filters.get("status", "ALL")
        if effective_status and effective_status != "ALL":
            clauses.append("COALESCE(NULLIF(a.build_verdict, ''), NULLIF(a.portfolio_status, ''), 'WATCH') = ?")
            params.append(effective_status)

        source = filters.get("source", "ALL")
        if source and source != "ALL":
            clauses.append("o.source = ?")
            params.append(source)

        topic = filters.get("topic", "ALL")
        if topic and topic != "ALL":
            normalizer = TopicNormalizer()
            search_terms = {topic}

            for alias, canonical in TopicNormalizer.ALIASES.items():
                if canonical.lower() == topic.lower():
                    search_terms.add(alias)

            topic_parts = []
            for term in sorted(search_terms):
                needle = f"%{term}%"
                topic_parts.append(
                    "(LOWER(COALESCE(a.topics, '')) LIKE LOWER(?) "
                    "OR LOWER(COALESCE(o.topics, '')) LIKE LOWER(?) "
                    "OR LOWER(COALESCE(a.category, '')) LIKE LOWER(?))"
                )
                params.extend([needle, needle, needle])

            clauses.append("(" + " OR ".join(topic_parts) + ")")

        if filters.get("min_cash"):
            clauses.append("a.cash_machine_score >= ?")
            params.append(int(filters["min_cash"]))

        if filters.get("max_rank"):
            clauses.append("a.ranking_score <= ?")
            params.append(int(filters["max_rank"]))

        if filters.get("date_from"):
            date_from = datetime.strptime(
                filters["date_from"],
                "%Y-%m-%d",
            )
            clauses.append("a.created_at >= ?")
            params.append(date_from)

        if filters.get("date_to"):
            date_to_exclusive = datetime.strptime(
                filters["date_to"],
                "%Y-%m-%d",
            ) + timedelta(days=1)
            clauses.append("a.created_at < ?")
            params.append(date_to_exclusive)

        return clauses, params

    def _query_bucket(
        self,
        status: str,
        limit: int = 24,
        filters: dict | None = None,
    ) -> list[dict]:
        filters = self._normalize_filters(filters)
        clauses, params = self._filter_clauses(filters, status=status)
        where_sql = " AND ".join(clauses)
        order_sql = self._order_by(filters["sort"])

        rows = self._query_all(
            f"""
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
                a.trend_score,
                a.portfolio_status,
                a.build_verdict,
                a.created_at AS analysis_created_at,
                CASE WHEN f.id IS NULL THEN 0 ELSE 1 END AS is_favorite
            FROM analyses a
            JOIN opportunities o
              ON o.id = a.opportunity_id
            LEFT JOIN favorite_opportunities f
              ON f.opportunity_id = a.opportunity_id
            WHERE {where_sql}
            ORDER BY {order_sql}
            LIMIT ?
            """,
            tuple(params + [limit]),
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
                    "trend_score": row.get("trend_score") or 0,
                    "portfolio_status": row.get("build_verdict") or row.get("portfolio_status") or "WATCH",
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
                        row.get("build_verdict") or row.get("portfolio_status")
                    ),
                    "is_favorite": bool(row.get("is_favorite")),
                }
            )

        return items

    def _count_bucket(self, status: str, filters: dict) -> int:
        clauses, params = self._filter_clauses(filters, status=status)
        where_sql = " AND ".join(clauses)

        row = self._query_all(
            f"""
            SELECT COUNT(*) AS total
            FROM analyses a
            JOIN opportunities o
              ON o.id = a.opportunity_id
            WHERE {where_sql}
            """,
            tuple(params),
        )

        return int(row[0].get("total") or 0) if row else 0

    def _get_filter_options(self) -> dict:
        sources_rows = self._query_all(
            """
            SELECT DISTINCT source
            FROM opportunities
            WHERE source IS NOT NULL AND TRIM(source) <> ''
            ORDER BY source ASC
            """
        )

        topic_rows = self._query_all(
            """
            SELECT a.topics, o.topics AS opportunity_topics, a.category
            FROM analyses a
            JOIN opportunities o ON o.id = a.opportunity_id
            WHERE a.ranking_score > 0
            """
        )

        normalizer = TopicNormalizer()
        topics = []
        seen = set()

        for row in topic_rows:
            candidates = []
            candidates.extend(self._parse_json_list(row.get("topics")))
            candidates.extend(self._parse_json_list(row.get("opportunity_topics")))
            candidates.extend(self._split_category(row.get("category")))

            for topic in candidates:
                normalized = normalizer.normalize(topic)
                if not normalized:
                    continue
                key = normalized.lower()
                if key in seen:
                    continue
                seen.add(key)
                topics.append(normalized)

        topics.sort(key=str.lower)

        return {
            "sources": [row["source"] for row in sources_rows if row.get("source")],
            "topics": topics,
            "statuses": ["ALL", "BUILD", "WATCH", "SKIP"],
            "sorts": [
                {"value": key, "label": label}
                for key, label in self.SORT_OPTIONS.items()
            ],
        }

    def get_feed_data(self, filters: dict | None = None) -> dict:

        filters = self._normalize_filters(filters)
        summary = self.dashboard_service.get_summary()
        hot_topics = self.dashboard_service.get_hot_topics(5)

        build_items = self._query_bucket("BUILD", 24, filters)
        watch_items = self._query_bucket("WATCH", 24, filters)
        skip_items = self._query_bucket("SKIP", 24, filters)

        sections = [
            {
                "label": "BUILD",
                "tone": "build",
                "description": "High-priority opportunities that deserve builder attention.",
                "count": self._count_bucket("BUILD", filters),
                "items": build_items,
                "empty_message": "No BUILD opportunities yet.",
            },
            {
                "label": "WATCH",
                "tone": "watch",
                "description": "Promising ideas worth monitoring until the signal gets stronger.",
                "count": self._count_bucket("WATCH", filters),
                "items": watch_items,
                "empty_message": "No WATCH opportunities yet.",
            },
            {
                "label": "SKIP",
                "tone": "skip",
                "description": "Ideas that are likely too weak or too crowded to pursue now.",
                "count": self._count_bucket("SKIP", filters),
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
            "filters": filters,
            "filter_options": self._get_filter_options(),
            "filtered_total": sum(
                section["count"]
                for section in sections
            ),
        }
