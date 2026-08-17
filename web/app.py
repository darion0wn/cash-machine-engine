from __future__ import annotations

import os
import subprocess
import sys
from datetime import date
from pathlib import Path

from flask import Flask, render_template

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from web.routes import register_routes  # noqa: E402
from web.services.scheduler_service import scheduler_service  # noqa: E402


APP_NAME = "Cash Machine Engine"
APP_DESCRIPTION = (
    "AI Founder Workspace that scans opportunities, scores them, tracks market "
    "momentum, and helps decide what is worth building."
)
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")


def _resolve_git_commit() -> str:
    override = os.getenv("APP_COMMIT") or os.getenv("GIT_COMMIT")
    if override:
        return override.strip()[:12]

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return "local"

    commit = result.stdout.strip()
    return commit or "local"


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
        static_url_path="/static",
    )

    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["JSON_SORT_KEYS"] = False

    register_routes(app)

    # The scheduler is an in-process background worker. In debug mode,
    # Werkzeug may spawn a reloader child, so only the serving process starts it.
    if os.getenv("FLASK_DEBUG", "0") != "1" or os.getenv("WERKZEUG_RUN_MAIN") == "true":
        scheduler_service.start()

    build_date = os.getenv("BUILD_DATE") or date.today().strftime("%d %b %Y")
    app_commit = _resolve_git_commit()

    @app.context_processor
    def inject_globals():
        return {
            "app_name": APP_NAME,
            "app_description": APP_DESCRIPTION,
            "app_version": APP_VERSION,
            "app_commit": app_commit,
            "build_date": build_date,
            "current_year": date.today().year,
        }

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template(
            "404.html",
            active_page=None,
            page_title="404 - Opportunity not found",
            page_description=(
                "The requested page could not be found inside the Founder "
                "Workspace."
            ),
        ), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template(
            "500.html",
            active_page=None,
            page_title="500 - Something went wrong",
            page_description=(
                "The Founder Workspace hit an unexpected error while rendering "
                "this page."
            ),
        ), 500

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
