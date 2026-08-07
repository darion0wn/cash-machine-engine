from __future__ import annotations

from .feed_service import FeedService


class PortfolioService(FeedService):
    SECTION_DEFINITIONS = (
        {
            "status": "BUILD",
            "label": "BUILD",
            "tone": "build",
            "description": "High-conviction opportunities ready for immediate action.",
            "empty_message": "No BUILD opportunities yet.",
        },
        {
            "status": "WATCH",
            "label": "WATCH",
            "tone": "watch",
            "description": "Promising ideas worth monitoring until the signal hardens.",
            "empty_message": "No WATCH opportunities yet.",
        },
        {
            "status": "SKIP",
            "label": "SKIP",
            "tone": "skip",
            "description": "Weak or crowded opportunities that should stay on the sidelines.",
            "empty_message": "No SKIP opportunities yet.",
        },
    )

    def _build_sections(
        self,
        summary: dict,
        limit_per_section: int,
    ) -> list[dict]:

        sections = []

        for definition in self.SECTION_DEFINITIONS:

            items = self._query_bucket(
                definition["status"],
                limit_per_section,
            )

            sections.append(
                {
                    "key": definition["status"].lower(),
                    "label": definition["label"],
                    "tone": definition["tone"],
                    "description": definition["description"],
                    "count": summary.get(
                        f"{definition['status'].lower()}_count",
                        0,
                    ) or 0,
                    "items": items,
                    "empty_message": definition["empty_message"],
                }
            )

        return sections

    @staticmethod
    def _pick_focus_item(sections: list[dict]) -> dict | None:

        for status in ("BUILD", "WATCH", "SKIP"):

            for section in sections:

                if section["key"] == status.lower() and section["items"]:
                    return section["items"][0]

        for section in sections:
            if section["items"]:
                return section["items"][0]

        return None

    def get_portfolio_data(self, limit_per_section: int = 6) -> dict:

        summary = self.dashboard_service.get_summary()
        sections = self._build_sections(
            summary,
            limit_per_section,
        )
        hot_topics = self.dashboard_service.get_hot_topics(5)
        recent_analyses = self.dashboard_service.get_recent_analyses(5)

        portfolio_focus_item = self._pick_focus_item(sections)

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
                "label": "Avg Rank",
                "value": f"{summary['avg_ranking_score']:.1f}",
                "hint": "Ranking engine average",
                "tone": "rank",
            },
            {
                "label": "Avg Cash",
                "value": f"{summary['avg_cash_score']:.1f}",
                "hint": "AI opportunity score",
                "tone": "cash",
            },
            {
                "label": "Topics",
                "value": summary["topics_count"],
                "hint": "Normalized hot topics",
                "tone": "topics",
            },
        ]

        top_topic = hot_topics[0] if hot_topics else None

        signal_rows = [
            {
                "label": "Analyses",
                "value": summary["total_analyses"],
            },
            {
                "label": "Sources",
                "value": summary["source_count"],
            },
            {
                "label": "Top topic",
                "value": top_topic["topic"] if top_topic else "None",
            },
            {
                "label": "Latest update",
                "value": summary["latest_analysis_at"] or "Unknown",
            },
        ]

        return {
            "summary": summary,
            "metrics": metrics,
            "sections": sections,
            "portfolio_focus_item": portfolio_focus_item,
            "signal_rows": signal_rows,
            "hot_topics": hot_topics,
            "recent_analyses": recent_analyses,
        }
