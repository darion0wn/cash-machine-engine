from flask import Blueprint, render_template, request, url_for

from web.services.dashboard_service import DashboardService
from web.services.feed_service import FeedService
from web.services.portfolio_service import PortfolioService
from web.services.reports_service import ReportsService
from web.services.trends_service import TrendsService

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
    feed_data = service.get_feed_data()

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
    portfolio_data = service.get_portfolio_data()

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


@pages_bp.route("/settings")
def settings():
    return _render_placeholder(
        "Settings",
        "Settings let you tune the dashboard, ranking and alerts in a later sprint.",
        "settings",
    )
