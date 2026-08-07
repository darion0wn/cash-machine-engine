from __future__ import annotations

from web.services.dashboard_service import DashboardService
from services.trend_engine import TrendEngine


class TrendsService:
    BAND_DEFINITIONS = (
        {
            "key": "exploding",
            "label": "Exploding",
            "icon": "🔥",
            "description": "Fast-rising topics with strong momentum and multi-source attention.",
            "tone": "exploding",
        },
        {
            "key": "growing",
            "label": "Growing",
            "icon": "📈",
            "description": "Themes that are strengthening and deserve active monitoring.",
            "tone": "growing",
        },
        {
            "key": "stable",
            "label": "Stable",
            "icon": "🟡",
            "description": "Topics with steady presence and consistent demand.",
            "tone": "stable",
        },
        {
            "key": "cooling",
            "label": "Cooling",
            "icon": "🧊",
            "description": "Signals that are fading or still too weak to prioritize.",
            "tone": "cooling",
        },
    )

    def __init__(self) -> None:
        self.dashboard_service = DashboardService()
        self.trend_engine = TrendEngine()

    @classmethod
    def _band_for_score(cls, score: float) -> dict:
        if score >= 70:
            return dict(cls.BAND_DEFINITIONS[0])
        if score >= 50:
            return dict(cls.BAND_DEFINITIONS[1])
        if score >= 35:
            return dict(cls.BAND_DEFINITIONS[2])
        return dict(cls.BAND_DEFINITIONS[3])

    @classmethod
    def _decorate_trend(cls, trend: dict) -> dict:
        band = cls._band_for_score(float(trend.get("trend_score") or 0))
        return {
            **trend,
            "band_key": band["key"],
            "band_label": band["label"],
            "band_icon": band["icon"],
            "band_tone": band["tone"],
            "meter_width": max(0.0, min(100.0, float(trend.get("trend_score") or 0))),
        }

    def get_trends_data(self, limit: int = 24) -> dict:
        summary = self.dashboard_service.get_summary()

        try:
            all_trends = self.trend_engine.trends()
        finally:
            self.trend_engine.repository.db.conn.close()

        trend_focus = self._decorate_trend(all_trends[0]) if all_trends else None
        trend_cards = [
            self._decorate_trend(trend)
            for trend in all_trends[:10]
        ]
        display_trends = all_trends[:limit]

        band_sections = [
            {
                **dict(band),
                "count": 0,
                "items": [],
            }
            for band in self.BAND_DEFINITIONS
        ]

        band_index = {band["key"]: band for band in band_sections}

        for trend in display_trends:
            decorated = self._decorate_trend(trend)
            band_bucket = band_index[decorated["band_key"]]

            band_bucket["count"] += 1

            if len(band_bucket["items"]) < 4:
                band_bucket["items"].append(decorated)

        band_counts = {
            band["key"]: band["count"]
            for band in band_sections
        }

        trend_metrics = [
            {
                "label": "Tracked Topics",
                "value": len(all_trends),
                "hint": "Normalized market themes",
                "tone": "topics",
            },
            {
                "label": "Top Trend",
                "value": f"{trend_focus['trend_score']:.1f}" if trend_focus else "0.0",
                "hint": trend_focus["topic"] if trend_focus else "No signals yet",
                "tone": "rank",
            },
            {
                "label": "Sources",
                "value": summary["source_count"],
                "hint": "Hacker News, GitHub, Product Hunt",
                "tone": "sources",
            },
            {
                "label": "Analyses",
                "value": summary["total_analyses"],
                "hint": "AI-evaluated opportunities",
                "tone": "analyses",
            },
        ]

        signal_rows = [
            {
                "label": "Exploding",
                "value": band_counts["exploding"],
                "hint": "High-momentum themes",
            },
            {
                "label": "Growing",
                "value": band_counts["growing"],
                "hint": "Topics getting stronger",
            },
            {
                "label": "Stable",
                "value": band_counts["stable"],
                "hint": "Signals worth tracking",
            },
            {
                "label": "Cooling",
                "value": band_counts["cooling"],
                "hint": "Signals fading or weak",
            },
        ]

        return {
            "summary": summary,
            "trend_focus": trend_focus,
            "trend_metrics": trend_metrics,
            "trend_cards": trend_cards,
            "trend_bands": band_sections,
            "signal_rows": signal_rows,
            "top_opportunities": self.dashboard_service.get_top_opportunities(limit=6),
            "recent_analyses": self.dashboard_service.get_recent_analyses(limit=5),
        }
