from flask import Blueprint, render_template, request

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


@pages_bp.route("/settings")
def settings():
    return _render_placeholder(
        "Settings",
        "Settings let you tune the dashboard, ranking and alerts in a later sprint.",
        "settings",
    )
