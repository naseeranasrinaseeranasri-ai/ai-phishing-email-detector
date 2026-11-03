from flask import Flask
from dotenv import load_dotenv

load_dotenv()  # reads settings from your .env file


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    from .routes import main
    app.register_blueprint(main)

    return app