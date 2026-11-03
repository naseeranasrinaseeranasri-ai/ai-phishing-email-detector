from flask import Blueprint, render_template, request
from .validation import validate_email_input

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html", values={}, errors={})


@main.route("/analyze", methods=["POST"])
def analyze():
    cleaned, errors = validate_email_input(
        request.form.get("sender"),
        request.form.get("subject"),
        request.form.get("body"),
    )

    if errors:
        # Show the form again with error messages and what the user typed
        return render_template("index.html", values=cleaned, errors=errors), 400

    # Temporary: just show the cleaned input. The rules and AI come later.
    return render_template("result.html", data=cleaned)