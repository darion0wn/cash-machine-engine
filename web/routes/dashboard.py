from flask import Blueprint, abort, render_template

from web.services.dashboard_service import DashboardService

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
def index():
    service = DashboardService()

    dashboard_data = service.get_dashboard_data()

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        page_title="Dashboard",
        **dashboard_data,
    )


@dashboard_bp.route("/opportunities/<int:opportunity_id>")
def detail(opportunity_id: int):
    service = DashboardService()

    detail_data = service.get_opportunity_detail(opportunity_id)

    if detail_data is None:
        abort(404)

    return render_template(
        "opportunity.html",
        active_page="dashboard",
        page_title=detail_data["opportunity"]["title"],
        detail=detail_data,
    )
