from __future__ import annotations

import json
import re
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

        parts = []

        for chunk in re.split(r"[\/,&|;]", category):

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

            merged_topics = self._merge_topics(
                analysis_topics,
                opportunity_topics,
                category_topics,
            )

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
                    "topics": merged_topics,
                    "category": row[8] or "",
                    "ranking_score": row[9] or 0,
                    "cash_machine_score": row[10] or 0,
                    "created_at": row[11],
                }
            )

        return documents