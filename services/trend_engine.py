from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from database.trend_repository import TrendRepository
from services.topic_normalizer import TopicNormalizer


class TrendEngine:

    def __init__(self):
        self.repository = TrendRepository()
        self.normalizer = TopicNormalizer()

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

        now = datetime.utcnow()
        days_ago = max(0, (now - latest_seen).days)

        return round(
            max(0.0, 30 - min(days_ago, 30)) / 3,
            1,
        )

    def _normalize_topics(self, topics):
        return self.normalizer.normalize_many(topics or [])

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
            topics = self._normalize_topics(
                document.get("topics") or []
            )

            if not topics:
                continue

            ranking_score = float(document.get("ranking_score") or 0)
            cash_score = float(document.get("cash_machine_score") or 0)
            source = document.get("source") or ""
            created_at = self._parse_datetime(document.get("created_at"))

            for topic in topics:
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
            recency_score = self._recency_score(stats["latest_seen"])

            raw_trend_score = (
                frequency * 7
                + average_ranking * 0.35
                + average_cash * 0.25
                + source_diversity * 4
                + recency_score
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
                    "trend_score": round(
                        min(100.0, raw_trend_score),
                        1,
                    ),
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

    def capture_snapshot(self) -> int:
        """
        Persist the current trend state. Intended to be called after a
        successful refresh, never during a normal page render.
        """
        return self.repository.save_snapshot(self.trends())

    def get_evolution(
        self,
        limit: int = 8,
        history_limit: int = 12,
    ) -> dict[str, Any]:
        current = self.trends()
        selected = current[:limit]
        topic_names = [item["topic"] for item in selected]

        history = self.repository.get_topic_history(
            topic_names,
            limit_snapshots=history_limit,
        )

        series = []

        for trend in selected:
            topic = trend["topic"]
            points = history.get(topic) or []

            previous = points[-2] if len(points) >= 2 else None
            latest = points[-1] if points else None

            score_change = None

            if previous is not None and latest is not None:
                score_change = round(
                    latest["trend_score"] - previous["trend_score"],
                    1,
                )

            series.append(
                {
                    "topic": topic,
                    "current_score": trend["trend_score"],
                    "frequency": trend["frequency"],
                    "source_diversity": trend["source_diversity"],
                    "latest_seen": trend["latest_seen"],
                    "points": points,
                    "has_history": len(points) >= 2,
                    "snapshot_count": len(points),
                    "score_change": score_change,
                }
            )

        return {
            "series": series,
            "snapshot_count": self.repository.snapshot_count(),
            "latest_snapshot_at": self.repository.latest_snapshot_at(),
            "has_history": any(
                item["has_history"]
                for item in series
            ),
        }
