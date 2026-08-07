from flask import Flask

from web.routes.dashboard import dashboard_bp
from web.routes.pages import pages_bp


def register_routes(app: Flask) -> None:
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(pages_bp)
