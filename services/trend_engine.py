from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from database.trend_repository import TrendRepository


class TrendEngine:

    def __init__(self):

        self.repository = TrendRepository()

    @staticmethod
    def _parse_datetime(value):

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

    @staticmethod
    def _recency_score(latest_seen):

        if latest_seen is None:
            return 0.0

        days_ago = max(0, (datetime.utcnow() - latest_seen).days)

        # Fresh topics get more credit, decaying over ~30 days.
        return round(max(0.0, 30 - min(days_ago, 30)) / 3, 1)

    def trends(self):

        documents = self.repository.all_documents()

        trends_by_topic = defaultdict(
            lambda: {
                "label": "",
                "frequency": 0,
                "ranking_sum": 0.0,
                "cash_sum": 0.0,
                "sources": set(),
                "latest_seen": None,
            }
        )

        for document in documents:

            topics = document.get("topics") or []

            if not topics:
                continue

            unique_topics = []

            seen = set()

            for topic in topics:

                if not topic:
                    continue

                normalized = str(topic).strip()

                if not normalized:
                    continue

                key = normalized.lower()

                if key in seen:
                    continue

                seen.add(key)
                unique_topics.append(normalized)

            if not unique_topics:
                continue

            ranking_score = float(document.get("ranking_score") or 0)
            cash_score = float(document.get("cash_machine_score") or 0)
            source = document.get("source") or ""
            created_at = self._parse_datetime(document.get("created_at"))

            for topic in unique_topics:

                key = topic.lower()
                stats = trends_by_topic[key]

                if not stats["label"]:
                    stats["label"] = topic

                stats["frequency"] += 1
                stats["ranking_sum"] += ranking_score
                stats["cash_sum"] += cash_score

                if source:
                    stats["sources"].add(source)

                if created_at and (
                    stats["latest_seen"] is None
                    or created_at > stats["latest_seen"]
                ):
                    stats["latest_seen"] = created_at

        trends = []

        for _, stats in trends_by_topic.items():

            frequency = stats["frequency"]

            if frequency <= 0:
                continue

            average_ranking = round(
                stats["ranking_sum"] / frequency,
                1,
            )

            average_cash = round(
                stats["cash_sum"] / frequency,
                1,
            )

            source_diversity = len(stats["sources"])

            recency_score = self._recency_score(
                stats["latest_seen"]
            )

            raw_trend_score = (
                frequency * 7
                + average_ranking * 0.35
                + average_cash * 0.25
                + source_diversity * 4
                + recency_score
            )

            trend_score = round(
                min(100.0, raw_trend_score),
                1,
            )

            trends.append(
                {
                    "topic": stats["label"],
                    "frequency": frequency,
                    "average_ranking": average_ranking,
                    "average_cash": average_cash,
                    "source_diversity": source_diversity,
                    "latest_seen": (
                        stats["latest_seen"].strftime("%Y-%m-%d")
                        if stats["latest_seen"]
                        else "Unknown"
                    ),
                    "trend_score": trend_score,
                }
            )

        trends.sort(
            key=lambda item: (
                item["trend_score"],
                item["frequency"],
                item["source_diversity"],
                item["average_ranking"],
            ),
            reverse=True,
        )

        return trends

    def top(self, limit: int = 20):

        return self.trends()[:limit]
