from flask import Blueprint, render_template

from web.services.feed_service import FeedService
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


@pages_bp.route("/feed")
def feed():
    service = FeedService()
    feed_data = service.get_feed_data()

    return render_template(
        "feed.html",
        active_page="feed",
        page_title="Feed",
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
        **trends_data,
    )


@pages_bp.route("/portfolio")
def portfolio():
    return _render_placeholder(
        "Portfolio",
        "The portfolio view will group opportunities into build now, watch and skip buckets.",
        "portfolio",
    )


@pages_bp.route("/reports")
def reports():
    return _render_placeholder(
        "Reports",
        "The reports viewer will expose generated Markdown reports directly in the browser.",
        "reports",
    )


@pages_bp.route("/settings")
def settings():
    return _render_placeholder(
        "Settings",
        "Settings will let you tune the dashboard, ranking and alerts in a later sprint.",
        "settings",
    )
