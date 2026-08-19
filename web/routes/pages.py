from flask import Blueprint, jsonify, render_template, request, url_for

from web.services.dashboard_service import DashboardService
from web.services.feed_service import FeedService
from web.services.favorites_service import FavoritesService
from web.services.portfolio_service import PortfolioService
from web.services.reports_service import ReportsService
from web.services.weekly_brief_service import WeeklyBriefService
from services.opportunity_lifecycle import OpportunityLifecycle
from web.services.trends_service import TrendsService
from services.evidence_tracker import EvidenceTracker
from services.founder_decision import FounderDecision
from web.services.comparison_service import ComparisonService

pages_bp = Blueprint("pages", __name__)


def _render_placeholder(
    page_title: str,
    page_description: str,
    active_page: str,
):
    return render_template(
        "page.html",
        page_title=page_title,
        page_description=page_description,
        active_page=active_page,
    )


def _render_reports(report_id: int | None = None):
    service = ReportsService()
    reports_data = service.get_reports_data(
        selected_report_id=report_id,
    )

    return render_template(
        "reports.html",
        active_page="reports",
        page_title="Reports",
        page_description=(
            "CEO briefing with archived analyses, market changes and "
            "recommended actions."
        ),
        **reports_data,
    )


@pages_bp.route("/feed")
def feed():
    service = FeedService()
    filters = {
        key: request.args.get(key, "")
        for key in service.FILTER_DEFAULTS
    }
    feed_data = service.get_feed_data(filters=filters)

    return render_template(
        "feed.html",
        active_page="feed",
        page_title="Feed",
        page_description=(
            "Decision feed with BUILD, WATCH and SKIP opportunities and "
            "market signals."
        ),
        **feed_data,
    )


@pages_bp.route("/trends")
def trends():
    service = TrendsService()
    trends_data = service.get_trends_data()

    return render_template(
        "trends.html",
        active_page="trends",
        page_title="Trends",
        page_description=(
            "Market radar with hot topics, momentum bands and related "
            "opportunities."
        ),
        **trends_data,
    )


@pages_bp.route("/portfolio")
def portfolio():
    service = PortfolioService()
    filters = {
        key: request.args.get(key, "")
        for key in service.FILTER_DEFAULTS
    }
    portfolio_data = service.get_portfolio_data(filters=filters)

    return render_template(
        "portfolio.html",
        active_page="portfolio",
        page_title="Portfolio",
        page_description=(
            "Founder portfolio workspace with BUILD, WATCH and SKIP buckets."
        ),
        **portfolio_data,
    )


@pages_bp.route("/reports")
def reports():
    selected_report_id = request.args.get(
        "report",
        type=int,
    )

    return _render_reports(selected_report_id)


@pages_bp.route("/reports/<int:report_id>")
def report_detail(report_id: int):
    return _render_reports(report_id)


@pages_bp.route("/about")
def about():
    return render_template(
        "about.html",
        active_page="about",
        page_title="About",
        page_description=(
            "Mission, workflow, stack and roadmap behind Cash Machine Engine."
        ),
    )


@pages_bp.route("/demo")
def demo():
    service = DashboardService()
    dashboard_data = service.get_dashboard_data()
    top_opportunities = dashboard_data.get("top_opportunities") or []
    summary = dashboard_data.get("summary") or {}
    sample_opportunity = top_opportunities[0] if top_opportunities else None

    sample_opportunity_href = (
        url_for(
            "dashboard.detail",
            opportunity_id=sample_opportunity["opportunity_id"],
        )
        if sample_opportunity
        else url_for("pages.feed")
    )

    demo_steps = [
        {
            "index": "01",
            "kicker": "Start here",
            "title": "Refresh data",
            "description": (
                "Load the latest signals to check pipeline health, hot "
                "topics and fresh opportunities."
            ),
            "href": url_for("dashboard.index"),
            "cta": "Open dashboard",
            "tone": "build",
        },
        {
            "index": "02",
            "kicker": "Find candidates",
            "title": "Review feed",
            "description": (
                "Scan BUILD, WATCH and SKIP opportunities in the daily "
                "decision feed."
            ),
            "href": url_for("pages.feed"),
            "cta": "Open feed",
            "tone": "watch",
        },
        {
            "index": "03",
            "kicker": "Go deep",
            "title": "Deep dive",
            "description": (
                f"Open {sample_opportunity['title']} to inspect the full analysis "
                "behind the ranking."
                if sample_opportunity
                else "Open a tracked opportunity to inspect the full analysis behind the ranking."
            ),
            "href": sample_opportunity_href,
            "cta": "Open opportunity",
            "tone": "detail",
        },
        {
            "index": "04",
            "kicker": "Check direction",
            "title": "Validate trends",
            "description": (
                "Confirm whether the market themes are heating up or "
                "cooling down."
            ),
            "href": url_for("pages.trends"),
            "cta": "Open trends",
            "tone": "trend",
        },
        {
            "index": "05",
            "kicker": "Sort the shortlist",
            "title": "Prioritize portfolio",
            "description": (
                "Bucket opportunities into BUILD, WATCH and SKIP before "
                "spending time on them."
            ),
            "href": url_for("pages.portfolio"),
            "cta": "Open portfolio",
            "tone": "portfolio",
        },
        {
            "index": "06",
            "kicker": "Close the loop",
            "title": "Read founder report",
            "description": (
                "Finish with the CEO-style briefing to decide what matters "
                "right now."
            ),
            "href": url_for("pages.reports"),
            "cta": "Open reports",
            "tone": "report",
        },
    ]

    demo_metrics = [
        {
            "label": "Playbook",
            "value": "6 steps",
            "hint": "Discovery → Decision",
            "tone": "flow",
        },
        {
            "label": "Focus",
            "value": summary.get("build_count", 0) or 0,
            "hint": "Build signals today",
            "tone": "build",
        },
        {
            "label": "Watch",
            "value": summary.get("watch_count", 0) or 0,
            "hint": "Ideas worth monitoring",
            "tone": "watch",
        },
        {
            "label": "Reports",
            "value": summary.get("total_analyses", 0) or 0,
            "hint": "Generated founder briefs",
            "tone": "report",
        },
    ]

    return render_template(
        "demo.html",
        active_page="demo",
        page_title="Founder Playbook",
        page_description=(
            "Private founder playbook that guides the daily workflow "
            "from discovery to decision."
        ),
        demo_steps=demo_steps,
        demo_metrics=demo_metrics,
        sample_opportunity=sample_opportunity,
        sample_opportunity_href=sample_opportunity_href,
    )


@pages_bp.route("/my-opportunities")
def my_opportunities():
    service = FavoritesService()
    data = service.get_my_opportunities()

    return render_template(
        "my_opportunities.html",
        active_page="favorites",
        page_title="My Opportunities",
        page_description=(
            "Private shortlist of opportunities worth keeping under observation."
        ),
        **data,
    )


@pages_bp.route("/favorites/<int:opportunity_id>/toggle", methods=["POST"])
def toggle_favorite(opportunity_id: int):
    payload = request.get_json(silent=True) or {}

    service = FavoritesService()
    is_favorite = service.toggle(
        opportunity_id=opportunity_id,
        cash_machine_score=int(payload.get("cash_machine_score", 0) or 0),
        ranking_score=int(payload.get("ranking_score", 0) or 0),
        portfolio_status=payload.get("portfolio_status"),
    )

    return jsonify(
        {
            "favorite": is_favorite,
            "count": service.get_count(),
            "opportunity_id": opportunity_id,
        }
    )


@pages_bp.route("/compare")
def compare():
    raw_ids = request.args.getlist("ids")
    if not raw_ids:
        raw = request.args.get("ids", "")
        raw_ids = [item.strip() for item in raw.split(",") if item.strip()]

    service = ComparisonService()
    try:
        data = service.get_comparison(raw_ids)
    finally:
        service.close()

    dashboard = DashboardService()
    selector = dashboard.get_top_opportunities(limit=12)

    return render_template(
        "compare.html",
        active_page="favorites",
        page_title="Compare Opportunities",
        page_description="Compare shortlisted opportunities using validation, evidence and the €500/month path.",
        selector=selector,
        **data,
    )


@pages_bp.route("/opportunities/<int:opportunity_id>/evidence", methods=["POST"])
def add_evidence(opportunity_id: int):
    payload = request.form if request.form else (request.get_json(silent=True) or {})
    validation_key = str(payload.get("validation_key", "")).strip()
    status = str(payload.get("status", "PARTIAL")).strip().upper()
    observation = str(payload.get("observation", "")).strip()
    source = str(payload.get("source", "")).strip()
    confidence = str(payload.get("confidence", "MEDIUM")).strip().upper()
    notes = str(payload.get("notes", "")).strip()

    if not validation_key or not observation:
        return jsonify({"ok": False, "error": "Validation step and observation are required."}), 400

    tracker = EvidenceTracker()
    try:
        evidence_id = tracker.add(
            opportunity_id,
            validation_key=validation_key,
            status=status,
            observation=observation,
            source=source,
            confidence=confidence,
            notes=notes,
        )
    except ValueError as exc:
        tracker.close()
        return jsonify({"ok": False, "error": str(exc)}), 400
    finally:
        try:
            tracker.close()
        except Exception:
            pass

    if request.is_json:
        return jsonify({"ok": True, "evidence_id": evidence_id})
    return __import__("flask").redirect(url_for("dashboard.detail", opportunity_id=opportunity_id))


@pages_bp.route("/opportunities/<int:opportunity_id>/decision", methods=["POST"])
def save_founder_decision(opportunity_id: int):
    payload = request.form if request.form else (request.get_json(silent=True) or {})
    decision = str(payload.get("decision", "WATCH")).strip().upper()
    rationale = str(payload.get("rationale", "")).strip()
    next_action = str(payload.get("next_action", "")).strip()

    service = FounderDecision()
    try:
        service.save_founder_decision(
            opportunity_id,
            decision,
            rationale,
            next_action,
        )
    except ValueError as exc:
        service.close()
        return jsonify({"ok": False, "error": str(exc)}), 400
    finally:
        try:
            service.close()
        except Exception:
            pass

    if request.is_json:
        return jsonify({"ok": True, "decision": decision})
    return __import__("flask").redirect(url_for("dashboard.detail", opportunity_id=opportunity_id))


@pages_bp.route("/weekly-brief")
def weekly_brief():
    service = WeeklyBriefService()
    data = service.build()
    return render_template(
        "weekly_brief.html",
        active_page="weekly_brief",
        page_title="Founder Weekly Brief",
        page_description=(
            "Private weekly brief focused on the opportunities and actions "
            "most likely to move the workspace toward €500/month."
        ),
        **data,
    )


@pages_bp.route("/opportunities/<int:opportunity_id>/lifecycle", methods=["POST"])
def transition_lifecycle(opportunity_id: int):
    payload = request.form if request.form else (request.get_json(silent=True) or {})
    stage = str(payload.get("stage", "ANALYZED")).strip().upper()
    reason = str(payload.get("reason", "")).strip()
    service = OpportunityLifecycle()
    try:
        lifecycle_id = service.transition(
            opportunity_id,
            stage=stage,
            reason=reason,
            source="founder",
        )
    except ValueError as exc:
        service.close()
        return jsonify({"ok": False, "error": str(exc)}), 400
    finally:
        try:
            service.close()
        except Exception:
            pass

    if request.is_json:
        return jsonify({"ok": True, "lifecycle_id": lifecycle_id, "stage": stage})
    return __import__("flask").redirect(url_for("dashboard.detail", opportunity_id=opportunity_id))


@pages_bp.route("/settings")
def settings():
    return _render_placeholder(
        "Settings",
        "Settings let you tune the dashboard, ranking and alerts in a later sprint.",
        "settings",
    )
