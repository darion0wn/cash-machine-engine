from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from database.database import Database


class TrendRepository:

    def __init__(self):
        self.db = Database()

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

        return [
            chunk.strip()
            for chunk in re.split(r"[\/,&|;]", category)
            if chunk.strip()
        ]

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

    def all_documents(self):

        cursor = self.db.conn.cursor()

        cursor.execute(
            """
            SELECT
                opportunities.id,
                opportunities.source,
                opportunities.title,
                opportunities.description,
                opportunities.website_text,
                opportunities.article,
                opportunities.topics AS opportunity_topics,
                analyses.topics AS analysis_topics,
                analyses.category,
                analyses.ranking_score,
                analyses.cash_machine_score,
                analyses.created_at
            FROM analyses
            INNER JOIN opportunities
                ON analyses.opportunity_id = opportunities.id
            ORDER BY analyses.id
            """
        )

        rows = cursor.fetchall()

        documents = []

        for row in rows:
            opportunity_topics = self._parse_json_list(row[6])
            analysis_topics = self._parse_json_list(row[7])
            category_topics = self._split_category(row[8])

            documents.append(
                {
                    "id": row[0],
                    "source": row[1] or "",
                    "title": row[2] or "",
                    "description": row[3] or "",
                    "website_text": row[4] or "",
                    "article": row[5] or "",
                    "opportunity_topics": opportunity_topics,
                    "analysis_topics": analysis_topics,
                    "topics": self._merge_topics(
                        analysis_topics,
                        opportunity_topics,
                        category_topics,
                    ),
                    "category": row[8] or "",
                    "ranking_score": row[9] or 0,
                    "cash_machine_score": row[10] or 0,
                    "created_at": row[11],
                }
            )

        return documents

    def save_snapshot(self, trends: list[dict[str, Any]]) -> int:
        """
        Persist one immutable market snapshot.

        Each successful refresh writes one row per currently tracked topic.
        No historical values are invented when no prior snapshot exists.
        """
        cursor = self.db.conn.cursor()

        captured_at = datetime.now().isoformat(timespec="microseconds")

        rows = [
            (
                captured_at,
                str(trend.get("topic") or "").strip(),
                int(trend.get("frequency") or 0),
                int(trend.get("source_diversity") or 0),
                float(trend.get("average_ranking") or 0),
                float(trend.get("average_cash") or 0),
                float(trend.get("trend_score") or 0),
            )
            for trend in trends
            if str(trend.get("topic") or "").strip()
        ]

        if rows:
            cursor.executemany(
                """
                INSERT INTO trend_snapshots (
                    captured_at,
                    topic,
                    frequency,
                    source_diversity,
                    average_ranking,
                    average_cash,
                    trend_score
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

        self.db.conn.commit()
        return len(rows)

    def snapshot_count(self) -> int:
        cursor = self.db.conn.cursor()
        row = cursor.execute(
            "SELECT COUNT(DISTINCT captured_at) FROM trend_snapshots"
        ).fetchone()
        return int(row[0] or 0)

    def latest_snapshot_at(self) -> str | None:
        cursor = self.db.conn.cursor()
        row = cursor.execute(
            """
            SELECT MAX(captured_at)
            FROM trend_snapshots
            """
        ).fetchone()

        return row[0] if row and row[0] else None

    def get_topic_history(
        self,
        topics: list[str],
        limit_snapshots: int = 12,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Return real persisted observations grouped by normalized topic.

        The caller provides canonical topic labels, and matching is
        case-insensitive. Results are ordered oldest → newest.
        """
        if not topics:
            return {}

        normalized_keys = {
            str(topic).strip().lower(): str(topic).strip()
            for topic in topics
            if str(topic).strip()
        }

        if not normalized_keys:
            return {}

        cursor = self.db.conn.cursor()

        placeholders = ", ".join("?" for _ in normalized_keys)

        rows = cursor.execute(
            f"""
            SELECT
                captured_at,
                topic,
                frequency,
                source_diversity,
                average_ranking,
                average_cash,
                trend_score
            FROM trend_snapshots
            WHERE LOWER(topic) IN ({placeholders})
            ORDER BY captured_at DESC, id DESC
            """,
            tuple(normalized_keys.keys()),
        ).fetchall()

        grouped: dict[str, list[dict[str, Any]]] = {
            canonical: []
            for canonical in normalized_keys.values()
        }

        seen_by_topic: dict[str, int] = {
            canonical: 0
            for canonical in normalized_keys.values()
        }

        for row in rows:
            canonical = normalized_keys.get(str(row[1]).strip().lower())

            if canonical is None:
                continue

            # One observation per topic per snapshot timestamp.
            timestamp_key = str(row[0])
            if any(
                str(item["captured_at"]) == timestamp_key
                for item in grouped[canonical]
            ):
                continue

            if seen_by_topic[canonical] >= limit_snapshots:
                continue

            grouped[canonical].append(
                {
                    "captured_at": row[0],
                    "frequency": int(row[2] or 0),
                    "source_diversity": int(row[3] or 0),
                    "average_ranking": float(row[4] or 0),
                    "average_cash": float(row[5] or 0),
                    "trend_score": float(row[6] or 0),
                }
            )

            seen_by_topic[canonical] += 1

        for values in grouped.values():
            values.reverse()

        return grouped
