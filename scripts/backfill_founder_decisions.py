from __future__ import annotations

import argparse
import json

from database.database import Database
from models.analysis import Analysis
from models.investment_recommendation import InvestmentRecommendation
from models.opportunity import Opportunity
from models.opportunity_status import OpportunityStatus
from services.autonomous_opportunity_pipeline import AutonomousOpportunityPipeline


def _parse_json(value, default):
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Re-sync existing analyses through the deterministic decision, "
            "lifecycle and optional Telegram alert workflow. No AI calls are made."
        )
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="Allow eligible opportunities to send Telegram alerts.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Process only the first N analyses. 0 means all analyses.",
    )
    return parser.parse_args()


def _load_rows(db, limit: int):
    query = """
        SELECT
            o.id, o.source, o.title, o.url, o.article, o.description,
            o.homepage, o.website_text, o.language, o.topics, o.license,
            o.stars, o.forks, o.watchers, o.open_issues, o.status,
            a.id, a.opportunity_id, a.model, a.prompt_version, a.problem,
            a.customer, a.ideal_customer, a.pain_level, a.urgency,
            a.current_solution, a.why_current_solution_fails, a.category,
            a.market_size, a.market_maturity, a.competition_level,
            a.competition, a.business_model, a.pricing_strategy,
            a.competitive_advantage, a.mvp_description,
            a.implementation_difficulty, a.monetization_difficulty,
            a.problem_score, a.market_score, a.competition_score,
            a.business_score, a.execution_score, a.ai_leverage_score,
            a.distribution_score, a.cash_machine_score, a.opportunity_score,
            a.build_verdict, a.investment_recommendation, a.confidence,
            a.confidence_reason, a.reasoning, a.key_evidence, a.red_flags,
            a.biggest_risk, a.next_action, a.recommended_next_steps,
            a.topics, a.trend_score, a.ranking_score, a.portfolio_status,
            a.created_at
        FROM analyses a
        JOIN opportunities o ON o.id = a.opportunity_id
        ORDER BY a.id
    """
    if limit > 0:
        query += " LIMIT ?"
        return db.conn.execute(query, (limit,)).fetchall()
    return db.conn.execute(query).fetchall()


def _build_models(row):
    opportunity = Opportunity(
        id=row[0], source=row[1], title=row[2], url=row[3], article=row[4] or "",
        description=row[5] or "", homepage=row[6], website_text=row[7] or "",
        language=row[8], topics=_parse_json(row[9], []), license=row[10],
        stars=row[11] or 0, forks=row[12] or 0, watchers=row[13] or 0,
        open_issues=row[14] or 0, status=OpportunityStatus(row[15]),
    )
    analysis = Analysis(
        id=row[16], opportunity_id=row[17], model=row[18], prompt_version=row[19],
        problem=row[20], customer=row[21], ideal_customer=row[22],
        pain_level=row[23], urgency=row[24], current_solution=row[25],
        why_current_solution_fails=row[26], category=row[27], market_size=row[28],
        market_maturity=row[29], competition_level=row[30], competition=row[31],
        business_model=row[32], pricing_strategy=row[33], competitive_advantage=row[34],
        mvp_description=row[35], implementation_difficulty=row[36],
        monetization_difficulty=row[37], problem_score=row[38], market_score=row[39],
        competition_score=row[40], business_score=row[41], execution_score=row[42],
        ai_leverage_score=row[43], distribution_score=row[44], cash_machine_score=row[45],
        opportunity_score=row[46], build_verdict=row[47],
        investment_recommendation=InvestmentRecommendation(row[48]), confidence=row[49],
        confidence_reason=row[50], reasoning=row[51], key_evidence=_parse_json(row[52], []),
        red_flags=_parse_json(row[53], []), biggest_risk=row[54], next_action=row[55],
        recommended_next_steps=row[56], topics=_parse_json(row[57], []),
        trend_score=row[58] or 0, ranking_score=row[59] or 0,
        portfolio_status=row[60] or "WATCH", created_at=row[61],
    )
    return opportunity, analysis


def main() -> int:
    args = _parse_args()
    db = Database()
    rows = _load_rows(db, args.limit)
    processed = 0
    failed = 0
    alerts_sent = 0
    alerts_skipped = 0

    for row in rows:
        opportunity_id = row[0]
        try:
            opportunity, analysis = _build_models(row)
            result = AutonomousOpportunityPipeline.process(
                opportunity,
                analysis,
                notify=args.notify,
                db=db,
            )
            alert = result.get("telegram_alert") or {}
            if alert.get("sent"):
                alerts_sent += 1
            elif args.notify:
                alerts_skipped += 1
            processed += 1
        except Exception as exc:
            failed += 1
            print(f"[WARN] Opportunity {opportunity_id} backfill failed: {exc}")

    db.conn.close()
    print(
        "Founder decision backfill completed: "
        f"processed={processed}, failed={failed}, "
        f"alerts_sent={alerts_sent}, alerts_skipped={alerts_skipped}, "
        f"notifications={'enabled' if args.notify else 'disabled'}"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
