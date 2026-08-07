from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from database.database import Database
from services.trend_engine import TrendEngine


class DashboardService:

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

    def _query_one(self, sql: str, params: tuple = ()) -> dict | None:

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
    def _recommendation_badge(value: str | None) -> str:

        mapping = {
            "STRONG_BUY": "🟢 STRONG BUY",
            "BUY": "🟢 BUY",
            "WATCH": "🟡 WATCH",
            "PASS": "❌ PASS",
        }

        return mapping.get((value or "").upper(), "Unknown")

    @staticmethod
    def _status_badge(value: str | None) -> str:

        mapping = {
            "BUILD": "🟢 BUILD",
            "WATCH": "🟡 WATCH",
            "SKIP": "❌ SKIP",
        }

        return mapping.get((value or "").upper(), value or "Unknown")

    def get_summary(self) -> dict:

        summary = self._query_one(
            """
            SELECT
                COUNT(*) AS total_analyses,
                COALESCE(ROUND(AVG(cash_machine_score), 1), 0) AS avg_cash_score,
                COALESCE(ROUND(AVG(ranking_score), 1), 0) AS avg_ranking_score,
                SUM(CASE WHEN portfolio_status = 'BUILD' THEN 1 ELSE 0 END) AS build_count,
                SUM(CASE WHEN portfolio_status = 'WATCH' THEN 1 ELSE 0 END) AS watch_count,
                SUM(CASE WHEN portfolio_status = 'SKIP' THEN 1 ELSE 0 END) AS skip_count,
                MAX(created_at) AS latest_analysis_at
            FROM analyses
            """
        ) or {}

        opportunities = self._query_one(
            """
            SELECT
                COUNT(*) AS total_opportunities,
                SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) AS pending_count,
                SUM(CASE WHEN status = 'PROCESSING' THEN 1 ELSE 0 END) AS processing_count,
                SUM(CASE WHEN status = 'DONE' THEN 1 ELSE 0 END) AS done_count,
                SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS failed_count
            FROM opportunities
            """
        ) or {}

        sources = self._query_one(
            """
            SELECT COUNT(DISTINCT source) AS source_count
            FROM opportunities
            """
        ) or {}

        trend_engine = TrendEngine()

        try:
            topics_count = len(trend_engine.trends())
        finally:
            trend_engine.repository.db.conn.close()

        hour = datetime.now().hour
        if 5 <= hour < 12:
            greeting = "Good morning, Dario."
        elif 12 <= hour < 18:
            greeting = "Good afternoon, Dario."
        elif 18 <= hour < 22:
            greeting = "Good evening, Dario."
        else:
            greeting = "Late-night hunting mode, Dario."

        return {
            "greeting": greeting,
            "total_opportunities": opportunities.get("total_opportunities", 0) or 0,
            "total_analyses": summary.get("total_analyses", 0) or 0,
            "build_count": summary.get("build_count", 0) or 0,
            "watch_count": summary.get("watch_count", 0) or 0,
            "skip_count": summary.get("skip_count", 0) or 0,
            "avg_cash_score": summary.get("avg_cash_score", 0) or 0,
            "avg_ranking_score": summary.get("avg_ranking_score", 0) or 0,
            "source_count": sources.get("source_count", 0) or 0,
            "topics_count": topics_count,
            "latest_analysis_at": self._format_datetime(
                summary.get("latest_analysis_at")
            ),
            "pending_count": opportunities.get("pending_count", 0) or 0,
            "processing_count": opportunities.get("processing_count", 0) or 0,
            "done_count": opportunities.get("done_count", 0) or 0,
            "failed_count": opportunities.get("failed_count", 0) or 0,
        }

    def get_summary_cards(self) -> list[dict]:

        summary = self.get_summary()

        return [
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
                "label": "Analyses",
                "value": summary["total_analyses"],
                "hint": "AI-evaluated opportunities",
                "tone": "analyses",
            },
            {
                "label": "Opportunities",
                "value": summary["total_opportunities"],
                "hint": "All discovered items",
                "tone": "opportunities",
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
                "label": "Sources",
                "value": summary["source_count"],
                "hint": "Hacker News, GitHub, Product Hunt",
                "tone": "sources",
            },
            {
                "label": "Topics",
                "value": summary["topics_count"],
                "hint": "Normalized hot topics",
                "tone": "topics",
            },
        ]

    def get_top_opportunities(self, limit: int = 10) -> list[dict]:

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
                a.cash_machine_score,
                a.ranking_score,
                a.portfolio_status,
                a.build_verdict,
                a.created_at AS analysis_created_at
            FROM analyses a
            JOIN opportunities o
              ON o.id = a.opportunity_id
            WHERE a.ranking_score > 0
            ORDER BY
                a.ranking_score DESC,
                a.cash_machine_score DESC,
                a.id DESC
            LIMIT ?
            """,
            (limit,),
        )

        items = []

        for row in rows:

            opportunity_topics = self._parse_json_list(
                row.get("opportunity_topics")
            )
            analysis_topics = self._parse_json_list(
                row.get("analysis_topics")
            )
            merged_topics = self._merge_topics(
                analysis_topics,
                opportunity_topics,
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
                    "status_badge": self._status_badge(
                        row.get("portfolio_status")
                    ),
                }
            )

        return items

    def get_recent_analyses(self, limit: int = 5) -> list[dict]:

        rows = self._query_all(
            """
            SELECT
                a.id AS analysis_id,
                a.opportunity_id,
                o.source,
                o.title,
                a.topics AS analysis_topics,
                a.category,
                a.cash_machine_score,
                a.ranking_score,
                a.portfolio_status,
                a.build_verdict,
                a.created_at AS analysis_created_at
            FROM analyses a
            JOIN opportunities o
              ON o.id = a.opportunity_id
            ORDER BY
                a.created_at DESC,
                a.id DESC
            LIMIT ?
            """,
            (limit,),
        )

        items = []

        for row in rows:

            analysis_topics = self._parse_json_list(
                row.get("analysis_topics")
            )

            items.append(
                {
                    "analysis_id": row.get("analysis_id"),
                    "opportunity_id": row.get("opportunity_id"),
                    "source": row.get("source") or "",
                    "title": row.get("title") or "",
                    "cash_machine_score": row.get("cash_machine_score") or 0,
                    "ranking_score": row.get("ranking_score") or 0,
                    "portfolio_status": row.get("portfolio_status") or "WATCH",
                    "build_verdict": row.get("build_verdict") or "Unknown",
                    "topic": self._primary_topic(
                        analysis_topics,
                        row.get("category") or "Unknown",
                    ),
                    "analysis_created_at": self._format_datetime(
                        row.get("analysis_created_at")
                    ),
                }
            )

        return items

    def get_hot_topics(self, limit: int = 5) -> list[dict]:

        trend_engine = TrendEngine()

        try:
            topics = trend_engine.top(limit)
        finally:
            trend_engine.repository.db.conn.close()

        return topics

    def get_opportunity_detail(
        self,
        opportunity_id: int,
    ) -> dict | None:

        row = self._query_one(
            """
            SELECT
                o.id AS opportunity_id,
                o.source,
                o.title,
                o.url,
                o.article,
                o.description,
                o.homepage,
                o.website_text,
                o.language,
                o.topics AS opportunity_topics,
                o.license,
                o.stars,
                o.forks,
                o.watchers,
                o.open_issues,
                o.status,
                o.created_at AS opportunity_created_at,
                o.updated_at,

                a.id AS analysis_id,
                a.model,
                a.prompt_version,
                a.problem,
                a.customer,
                a.ideal_customer,
                a.pain_level,
                a.urgency,
                a.current_solution,
                a.why_current_solution_fails,
                a.category,
                a.market_size,
                a.market_maturity,
                a.competition_level,
                a.competition,
                a.business_model,
                a.pricing_strategy,
                a.competitive_advantage,
                a.mvp_description,
                a.implementation_difficulty,
                a.monetization_difficulty,
                a.problem_score,
                a.market_score,
                a.competition_score,
                a.business_score,
                a.execution_score,
                a.ai_leverage_score,
                a.distribution_score,
                a.cash_machine_score,
                a.opportunity_score,
                a.build_verdict,
                a.investment_recommendation,
                a.confidence,
                a.confidence_reason,
                a.reasoning,
                a.key_evidence,
                a.red_flags,
                a.biggest_risk,
                a.next_action,
                a.recommended_next_steps,
                a.topics AS analysis_topics,
                a.trend_score,
                a.ranking_score,
                a.portfolio_status,
                a.created_at AS analysis_created_at

            FROM opportunities o

            LEFT JOIN analyses a
              ON a.opportunity_id = o.id

            WHERE o.id = ?

            ORDER BY a.id DESC
            LIMIT 1
            """,
            (opportunity_id,),
        )

        if row is None:
            return None

        opportunity_topics = self._parse_json_list(
            row.get("opportunity_topics")
        )
        analysis_topics = self._parse_json_list(
            row.get("analysis_topics")
        )
        merged_topics = self._merge_topics(
            analysis_topics,
            opportunity_topics,
        )

        opportunity = {
            "id": row.get("opportunity_id"),
            "source": row.get("source") or "",
            "title": row.get("title") or "",
            "url": row.get("url") or "",
            "article": row.get("article") or "",
            "description": row.get("description") or "",
            "homepage": row.get("homepage") or "",
            "website_text": row.get("website_text") or "",
            "language": row.get("language") or "",
            "topics": merged_topics,
            "license": row.get("license") or "",
            "stars": row.get("stars") or 0,
            "forks": row.get("forks") or 0,
            "watchers": row.get("watchers") or 0,
            "open_issues": row.get("open_issues") or 0,
            "status": row.get("status") or "PENDING",
            "created_at": self._format_datetime(
                row.get("opportunity_created_at")
            ),
            "updated_at": self._format_datetime(
                row.get("updated_at")
            ),
            "topic_label": self._primary_topic(
                merged_topics,
                "Unknown",
            ),
        }

        analysis = None

        if row.get("analysis_id") is not None:

            key_evidence = self._parse_json_list(
                row.get("key_evidence")
            )
            red_flags = self._parse_json_list(
                row.get("red_flags")
            )

            analysis_topics_list = self._merge_topics(
                analysis_topics,
                opportunity_topics,
            )

            analysis = {
                "id": row.get("analysis_id"),
                "model": row.get("model") or "",
                "prompt_version": row.get("prompt_version") or "",
                "problem": row.get("problem") or "",
                "customer": row.get("customer") or "",
                "ideal_customer": row.get("ideal_customer") or "",
                "pain_level": row.get("pain_level") or 0,
                "urgency": row.get("urgency") or 0,
                "current_solution": row.get("current_solution") or "",
                "why_current_solution_fails": row.get("why_current_solution_fails") or "",
                "category": row.get("category") or "",
                "market_size": row.get("market_size") or "",
                "market_maturity": row.get("market_maturity") or "",
                "competition_level": row.get("competition_level") or 0,
                "competition": row.get("competition") or "",
                "business_model": row.get("business_model") or "",
                "pricing_strategy": row.get("pricing_strategy") or "",
                "competitive_advantage": row.get("competitive_advantage") or "",
                "mvp_description": row.get("mvp_description") or "",
                "implementation_difficulty": row.get("implementation_difficulty") or 0,
                "monetization_difficulty": row.get("monetization_difficulty") or 0,
                "problem_score": row.get("problem_score") or 0,
                "market_score": row.get("market_score") or 0,
                "competition_score": row.get("competition_score") or 0,
                "business_score": row.get("business_score") or 0,
                "execution_score": row.get("execution_score") or 0,
                "ai_leverage_score": row.get("ai_leverage_score") or 0,
                "distribution_score": row.get("distribution_score") or 0,
                "cash_machine_score": row.get("cash_machine_score") or 0,
                "opportunity_score": row.get("opportunity_score") or 0,
                "build_verdict": row.get("build_verdict") or "Unknown",
                "investment_recommendation": self._recommendation_badge(
                    row.get("investment_recommendation")
                ),
                "confidence": row.get("confidence") or 0,
                "confidence_reason": row.get("confidence_reason") or "",
                "reasoning": row.get("reasoning") or "",
                "key_evidence": key_evidence,
                "red_flags": red_flags,
                "biggest_risk": row.get("biggest_risk") or "",
                "next_action": row.get("next_action") or "",
                "recommended_next_steps": row.get("recommended_next_steps") or "",
                "topics": analysis_topics_list,
                "topic_label": self._primary_topic(
                    analysis_topics_list,
                    row.get("category") or "Unknown",
                ),
                "trend_score": row.get("trend_score") or 0,
                "ranking_score": row.get("ranking_score") or 0,
                "portfolio_status": row.get("portfolio_status") or "WATCH",
                "portfolio_badge": self._status_badge(
                    row.get("portfolio_status")
                ),
                "created_at": self._format_datetime(
                    row.get("analysis_created_at")
                ),
            }

            analysis["score_breakdown"] = [
                {"label": "Problem", "value": analysis["problem_score"]},
                {"label": "Market", "value": analysis["market_score"]},
                {"label": "Competition", "value": analysis["competition_score"]},
                {"label": "Business", "value": analysis["business_score"]},
                {"label": "Execution", "value": analysis["execution_score"]},
                {"label": "AI Leverage", "value": analysis["ai_leverage_score"]},
                {"label": "Distribution", "value": analysis["distribution_score"]},
            ]

        return {
            "opportunity": opportunity,
            "analysis": analysis,
        }

    def get_dashboard_data(self) -> dict:

        summary = self.get_summary()

        return {
            "summary": summary,
            "summary_cards": self.get_summary_cards(),
            "top_opportunities": self.get_top_opportunities(limit=10),
            "hot_topics": self.get_hot_topics(limit=5),
            "recent_analyses": self.get_recent_analyses(limit=5),
        }
