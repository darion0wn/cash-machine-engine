from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import mistune

from .dashboard_service import DashboardService
from database.database import Database


class ReportsService:
    REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports" / "markdown"

    def __init__(self) -> None:
        self.dashboard_service = DashboardService()
        self._markdown = mistune.create_markdown(
            escape=True,
            plugins=["table"],
        )

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
                "%d %b %Y %H:%M",
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
    def _compact_text(value: Any, limit: int = 160) -> str:

        if value is None:
            return ""

        text = " ".join(str(value).split()).strip()

        if not text:
            return ""

        if len(text) <= limit:
            return text

        return text[: limit - 1].rstrip() + "…"

    @staticmethod
    def _extract_table_value(content: str, field: str) -> str:

        pattern = rf"^\|\s*{re.escape(field)}\s*\|\s*(.*?)\s*\|$"
        match = re.search(pattern, content, flags=re.MULTILINE)

        if not match:
            return ""

        return match.group(1).strip()

    @staticmethod
    def _extract_scalar(content: str, pattern: str, default: str = "") -> str:

        match = re.search(pattern, content, flags=re.MULTILINE)

        if not match:
            return default

        return match.group(1).strip()

    @classmethod
    def _extract_section(cls, content: str, heading: str) -> str:

        pattern = rf"(?ms)^#+\s*{re.escape(heading)}\s*$\n+(.*?)(?=^#+\s|\Z)"
        match = re.search(pattern, content)

        if not match:
            return ""

        return match.group(1).strip()

    @classmethod
    def _extract_section_excerpt(
        cls,
        content: str,
        heading: str,
        limit: int = 180,
    ) -> str:

        section = cls._extract_section(content, heading)

        if not section:
            return ""

        return cls._compact_text(section, limit=limit)

    @staticmethod
    def _status_badge(value: str | None) -> str:

        mapping = {
            "BUILD": "🟢 BUILD",
            "WATCH": "🟡 WATCH",
            "SKIP": "❌ SKIP",
        }

        return mapping.get((value or "").upper(), value or "Unknown")

    @staticmethod
    def _verdict_tone(value: str | None) -> str:

        mapping = {
            "BUILD": "build",
            "WATCH": "watch",
            "SKIP": "skip",
        }

        return mapping.get((value or "").upper(), "watch")

    def _report_paths(self) -> list[Path]:

        if not self.REPORTS_DIR.exists():
            return []

        paths = list(self.REPORTS_DIR.glob("*.md"))

        def sort_key(path: Path) -> tuple[float, int]:

            try:
                mtime = path.stat().st_mtime
            except OSError:
                mtime = 0.0

            try:
                report_id = int(path.stem)
            except ValueError:
                report_id = 0

            return (mtime, report_id)

        return sorted(
            paths,
            key=sort_key,
            reverse=True,
        )

    def _build_report_card(
        self,
        path: Path,
        include_html: bool = False,
    ) -> dict:

        content = path.read_text(encoding="utf-8")

        try:
            report_id = int(path.stem)
        except ValueError:
            report_id = 0

        source = self._extract_table_value(content, "Source") or "Unknown"
        title = self._extract_table_value(content, "Title") or f"Report #{report_id or path.stem}"
        url = self._extract_table_value(content, "URL") or ""
        cash_machine_score = self._extract_scalar(
            content,
            r"(?m)^#\s*(\d+)\s*/\s*100\s*$",
            default="0",
        )
        verdict = self._extract_scalar(
            content,
            r"\*\*Verdict:\*\*\s*([^\n]+)",
            default="Unknown",
        )
        recommendation = self._extract_scalar(
            content,
            r"\*\*Investment Recommendation:\*\*\s*([^\n]+)",
            default="Unknown",
        )
        confidence = self._extract_scalar(
            content,
            r"\*\*Confidence:\*\*\s*([0-9]+)\s*(?:%|/10)?",
            default="0",
        )
        opportunity_id = self._extract_scalar(
            content,
            r"^\|\s*Opportunity ID\s*\|\s*([0-9]+)\s*\|$",
            default=str(report_id or 0),
        )
        generated_at = self._extract_scalar(
            content,
            r"^\|\s*Generated At\s*\|\s*(.*?)\s*\|$",
            default="",
        )

        if not generated_at:
            try:
                generated_at = self._format_datetime(
                    datetime.fromtimestamp(path.stat().st_mtime)
                )
            except OSError:
                generated_at = "Unknown"

        reasoning_excerpt = self._extract_section_excerpt(
            content,
            "Full Reasoning",
            limit=180,
        )
        if not reasoning_excerpt:
            reasoning_excerpt = self._extract_section_excerpt(
                content,
                "Confidence Reason",
                limit=180,
            )

        next_action = self._extract_section_excerpt(
            content,
            "Next Action",
            limit=220,
        )
        biggest_risk = self._extract_section_excerpt(
            content,
            "Biggest Risk",
            limit=220,
        )
        recommended_next_steps = self._extract_section_excerpt(
            content,
            "Recommended Next Steps",
            limit=220,
        )

        report = {
            "id": report_id,
            "opportunity_id": int(opportunity_id or 0),
            "title": title,
            "source": source,
            "url": url,
            "cash_machine_score": int(cash_machine_score or 0),
            "verdict": verdict,
            "recommendation": recommendation,
            "confidence": int(confidence or 0),
            "generated_at": generated_at,
            "reasoning_excerpt": reasoning_excerpt,
            "next_action": next_action,
            "biggest_risk": biggest_risk,
            "recommended_next_steps": recommended_next_steps,
            "tone": self._verdict_tone(verdict),
            "status_badge": self._status_badge(verdict),
        }

        if include_html:
            report["html"] = self._markdown(content)
            report["content"] = content

        return report

    @staticmethod
    def _decode_list(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except (TypeError, json.JSONDecodeError):
                return []
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        return []

    @classmethod
    def _database_report_content(cls, row: dict[str, Any]) -> str:
        key_evidence = cls._decode_list(row.get("key_evidence"))
        red_flags = cls._decode_list(row.get("red_flags"))
        topics = cls._decode_list(row.get("topics"))
        recommendation = str(row.get("investment_recommendation") or "Unknown")
        generated_at = cls._format_datetime(row.get("created_at"))
        bullets = lambda values: "\n".join(f"- {value}" for value in values) or "- None recorded"
        topic_bullets = "\n".join(f"- {value}" for value in topics) or "- Unknown"
        return f"""# {int(row.get('cash_machine_score') or 0)} / 100

**Verdict:** {row.get('build_verdict') or 'Unknown'}

**Investment Recommendation:** {recommendation}

**Confidence:** {int(row.get('confidence') or 0)}/10

| Field | Value |
|-------|-------|
| Opportunity ID | {row.get('opportunity_id')} |
| Title | {row.get('title') or 'Unknown'} |
| Source | {row.get('source') or 'Unknown'} |
| URL | {row.get('url') or 'N/A'} |
| Generated At | {generated_at} |

## Problem Analysis

### Problem
{row.get('problem') or 'Unknown'}

### Customer
{row.get('customer') or 'Unknown'}

### Ideal Customer
{row.get('ideal_customer') or 'Unknown'}

| Metric | Value |
|-------|------:|
| Pain Level | {int(row.get('pain_level') or 0)}/10 |
| Urgency | {int(row.get('urgency') or 0)}/10 |

### Current Solution
{row.get('current_solution') or 'Unknown'}

### Why Current Solution Fails
{row.get('why_current_solution_fails') or 'Unknown'}

## Market Analysis

**Category:** {row.get('category') or 'Unknown'}

**Market Size:** {row.get('market_size') or 'Unknown'}

**Market Maturity:** {row.get('market_maturity') or 'Unknown'}

**Competition Level:** {int(row.get('competition_level') or 0)}/10

### Competitors
{row.get('competition') or 'Unknown'}

## Business Analysis

### Business Model
{row.get('business_model') or 'Unknown'}

### Pricing Strategy
{row.get('pricing_strategy') or 'Unknown'}

### Competitive Advantage
{row.get('competitive_advantage') or 'Unknown'}

### MVP Description
{row.get('mvp_description') or 'Unknown'}

## Investment Evaluation

| Category | Score |
|----------|------:|
| Problem | {int(row.get('problem_score') or 0)}/10 |
| Market | {int(row.get('market_score') or 0)}/10 |
| Competition | {int(row.get('competition_score') or 0)}/10 |
| Business | {int(row.get('business_score') or 0)}/10 |
| Execution | {int(row.get('execution_score') or 0)}/10 |
| AI Leverage | {int(row.get('ai_leverage_score') or 0)}/10 |
| Distribution | {int(row.get('distribution_score') or 0)}/10 |

## Cash Machine Score

**{int(row.get('cash_machine_score') or 0)}/100**

**Build Verdict:** {row.get('build_verdict') or 'Unknown'}

**Confidence:** {int(row.get('confidence') or 0)}/10

### Confidence Reason
{row.get('confidence_reason') or 'Unknown'}

### Full Reasoning
{row.get('reasoning') or 'Unknown'}

## Key Evidence
{bullets(key_evidence)}

## Red Flags
{bullets(red_flags)}

## Biggest Risk
{row.get('biggest_risk') or 'Unknown'}

## Next Action
{row.get('next_action') or 'Unknown'}

## Recommended Next Steps
{row.get('recommended_next_steps') or 'Unknown'}

## Topics
{topic_bullets}
"""

    def _database_reports(self) -> list[dict]:
        db = Database()
        try:
            cursor = db.conn.execute(
                """
                SELECT a.*, o.source, o.title, o.url
                FROM analyses a
                JOIN opportunities o ON o.id = a.opportunity_id
                ORDER BY a.created_at DESC, a.id DESC
                """
            )
            columns = [d[0] for d in cursor.description or []]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            db.conn.close()

        reports: list[dict] = []
        seen: set[int] = set()
        for row in rows:
            opportunity_id = int(row.get("opportunity_id") or 0)
            if opportunity_id in seen:
                continue
            seen.add(opportunity_id)
            content = self._database_report_content(row)
            verdict = str(row.get("build_verdict") or "Unknown")
            reports.append(
                {
                    "id": opportunity_id,
                    "opportunity_id": opportunity_id,
                    "title": row.get("title") or f"Report #{opportunity_id}",
                    "source": row.get("source") or "Unknown",
                    "url": row.get("url") or "",
                    "cash_machine_score": int(row.get("cash_machine_score") or 0),
                    "verdict": verdict,
                    "recommendation": str(row.get("investment_recommendation") or "Unknown"),
                    "confidence": int(row.get("confidence") or 0),
                    "generated_at": self._format_datetime(row.get("created_at")),
                    "reasoning_excerpt": self._compact_text(row.get("reasoning"), 180),
                    "next_action": self._compact_text(row.get("next_action"), 220),
                    "biggest_risk": self._compact_text(row.get("biggest_risk"), 220),
                    "recommended_next_steps": self._compact_text(row.get("recommended_next_steps"), 220),
                    "tone": self._verdict_tone(verdict),
                    "status_badge": self._status_badge(verdict),
                    "content": content,
                    "html": self._markdown(content),
                }
            )
        return reports

    def list_reports(self) -> list[dict]:
        report_paths = self._report_paths()
        if report_paths:
            return [
                self._build_report_card(path, include_html=False)
                for path in report_paths
            ]
        return self._database_reports()

    def get_report(self, report_id: int | None = None) -> dict | None:
        report_paths = self._report_paths()
        if report_paths:
            selected_path = None
            if report_id is not None:
                for path in report_paths:
                    try:
                        current_id = int(path.stem)
                    except ValueError:
                        continue
                    if current_id == report_id:
                        selected_path = path
                        break
            selected_path = selected_path or report_paths[0]
            return self._build_report_card(selected_path, include_html=True)

        reports = self._database_reports()
        if not reports:
            return None
        if report_id is not None:
            for report in reports:
                if report["id"] == report_id:
                    return report
        return reports[0]

    def get_reports_data(self, selected_report_id: int | None = None) -> dict:

        summary = self.dashboard_service.get_summary()
        reports = self.list_reports()
        selected_report = self.get_report(selected_report_id)

        top_topics = self.dashboard_service.get_hot_topics(1)
        top_topic = top_topics[0] if top_topics else None

        confidence_values = [report["confidence"] for report in reports]
        avg_confidence = (
            round(sum(confidence_values) / len(confidence_values), 1)
            if confidence_values
            else 0.0
        )

        source_breakdown_counter = Counter(
            report["source"] for report in reports if report["source"]
        )
        source_breakdown = [
            {
                "source": source,
                "count": count,
            }
            for source, count in source_breakdown_counter.most_common(5)
        ]

        report_count = len(reports)

        selected_cash = (
            selected_report["cash_machine_score"]
            if selected_report
            else 0
        )
        selected_confidence = (
            selected_report["confidence"]
            if selected_report
            else 0
        )

        if report_count == 0:
            executive_brief = (
                "No markdown reports have been generated yet. "
                "Run the crawler to start filling the archive."
            )
        else:
            brief_parts = [
                f"The archive currently contains {report_count} generated reports.",
                f"{summary['build_count']} BUILD, {summary['watch_count']} WATCH and {summary['skip_count']} SKIP decisions are available.",
                f"The selected report scores {selected_cash}/100 with {selected_confidence}% confidence.",
            ]

            if top_topic:
                brief_parts.append(
                    f"Top topic right now: {top_topic['topic']} ({top_topic['trend_score']:.1f})."
                )

            if selected_report:
                brief_parts.append(
                    f"Currently viewing #{selected_report['opportunity_id']} · {selected_report['source']}."
                )

            executive_brief = " ".join(brief_parts)

        latest_report = reports[0] if reports else None

        metrics = [
            {
                "label": "Reports",
                "value": report_count,
                "hint": "Generated markdown reports",
                "tone": "reports",
            },
            {
                "label": "Selected Cash",
                "value": selected_cash,
                "hint": "Cash Machine score",
                "tone": "cash",
            },
            {
                "label": "Selected Confidence",
                "value": f"{selected_confidence}%",
                "hint": "Model confidence on this report",
                "tone": "confidence",
            },
            {
                "label": "BUILD",
                "value": summary["build_count"],
                "hint": "High-conviction opportunities",
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
        ]

        return {
            "summary": summary,
            "reports": reports,
            "selected_report": selected_report,
            "report_count": report_count,
            "latest_report": latest_report,
            "top_topic": top_topic,
            "source_breakdown": source_breakdown,
            "metrics": metrics,
            "avg_confidence": avg_confidence,
            "executive_brief": executive_brief,
        }
