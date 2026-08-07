from __future__ import annotations

import os
import sys
from pathlib import Path

from flask import Flask, render_template

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from web.routes import register_routes  # noqa: E402


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

    @app.context_processor
    def inject_globals():
        return {
            "app_name": "Cash Machine Engine",
            "current_year": 2026,
        }

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template(
            "404.html",
            active_page=None,
            page_title="404 - Opportunity not found",
        ), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template(
            "500.html",
            active_page=None,
            page_title="500 - Something went wrong",
        ), 500

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
