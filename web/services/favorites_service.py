from __future__ import annotations

import json
from datetime import datetime

from database.database import Database
from database.favorite_repository import FavoriteRepository


class FavoritesService:

    def __init__(self):
        self.repository = FavoriteRepository()

    @staticmethod
    def _format_datetime(value) -> str:
        if not value:
            return "Unknown"

        if isinstance(value, datetime):
            return value.strftime("%d %b %Y · %H:%M")

        text = str(value).strip()

        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return parsed.strftime("%d %b %Y · %H:%M")
        except ValueError:
            return text

    @staticmethod
    def _parse_topics(value) -> list[str]:
        if not value:
            return []

        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]

        try:
            parsed = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return []

        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]

        return []

    def toggle(
        self,
        opportunity_id: int,
        *,
        cash_machine_score: int = 0,
        ranking_score: int = 0,
        portfolio_status: str | None = None,
    ) -> bool:
        return self.repository.toggle(
            opportunity_id=opportunity_id,
            cash_machine_score=cash_machine_score,
            ranking_score=ranking_score,
            portfolio_status=portfolio_status,
        )

    def is_favorite(self, opportunity_id: int) -> bool:
        return self.repository.is_favorite(opportunity_id)

    def get_count(self) -> int:
        return self.repository.count()

    def get_my_opportunities(self) -> dict:
        rows = self.repository.list_with_current_analysis()

        items = []

        for row in rows:
            topics = self._parse_topics(row.get("topics"))

            items.append(
                {
                    "favorite_id": row.get("favorite_id"),
                    "opportunity_id": row.get("opportunity_id"),
                    "title": row.get("title") or "Untitled opportunity",
                    "source": row.get("source") or "Unknown",
                    "url": row.get("url") or "",
                    "saved_at": self._format_datetime(row.get("saved_at")),
                    "cash_machine_score": row.get("cash_machine_score") or 0,
                    "ranking_score": row.get("ranking_score") or 0,
                    "trend_score": row.get("trend_score") or 0,
                    "portfolio_status": row.get("build_verdict") or row.get("portfolio_status") or "WATCH",
                    "build_verdict": row.get("build_verdict") or "Unknown",
                    "primary_topic": topics[0] if topics else (row.get("category") or "Unknown"),
                    "topics": topics,
                    "next_action": row.get("next_action") or "Review the opportunity detail.",
                    "biggest_risk": row.get("biggest_risk") or "No risk captured yet.",
                    "analysis_created_at": self._format_datetime(
                        row.get("analysis_created_at")
                    ),
                    "cash_at_save": row.get("cash_machine_score_at_save") or 0,
                    "rank_at_save": row.get("ranking_score_at_save") or 0,
                }
            )

        metrics = {
            "total": len(items),
            "build": sum(1 for item in items if item["portfolio_status"] == "BUILD"),
            "watch": sum(1 for item in items if item["portfolio_status"] == "WATCH"),
            "skip": sum(1 for item in items if item["portfolio_status"] == "SKIP"),
        }

        return {
            "items": items,
            "metrics": metrics,
        }
