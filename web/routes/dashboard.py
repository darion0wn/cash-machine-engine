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
        page_description=(
            "Live founder dashboard with BUILD, WATCH and SKIP signals, "
            "hot topics and recent analyses."
        ),
        **dashboard_data,
    )


@dashboard_bp.route("/opportunities/<int:opportunity_id>")
def detail(opportunity_id: int):
    service = DashboardService()

    detail_data = service.get_opportunity_detail(opportunity_id)

    if detail_data is None:
        abort(404)

    opportunity = detail_data.get("opportunity", {})
    analysis = detail_data.get("analysis") or {}

    topic = opportunity.get("topic_label") or analysis.get("topic_label") or "opportunity"
    source = opportunity.get("source") or "tracked source"
    cash_score = analysis.get("cash_machine_score")

    description_parts = [
        f"{source} opportunity focused on {topic}.",
    ]

    if cash_score is not None:
        description_parts.append(f"Cash score: {cash_score}.")

    return render_template(
        "opportunity.html",
        active_page="dashboard",
        page_title=opportunity.get("title") or "Opportunity",
        page_description=" ".join(description_parts),
        detail=detail_data,
    )
