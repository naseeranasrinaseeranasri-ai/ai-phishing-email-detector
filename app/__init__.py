import logging

from dotenv import load_dotenv
from flask import Flask

load_dotenv()  # reads settings from your .env file


def create_app():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    # Reject huge requests before they are processed (100 KB)
    app.config["MAX_CONTENT_LENGTH"] = 100 * 1024

    @app.after_request
    def set_security_headers(resp):
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'")
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        return resp

    from .database import init_db
    init_db()

    from .routes import main
    app.register_blueprint(main)

    return app