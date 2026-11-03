from flask import Blueprint, render_template, request
from .validation import validate_email_input
from .rules import analyze_rules
from .ollama_client import analyze_with_ai
from .scoring import combine

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
        return render_template("index.html", values=cleaned, errors=errors), 400

    rules = analyze_rules(cleaned["sender"], cleaned["subject"], cleaned["body"])
    ai_response = analyze_with_ai(cleaned["sender"], cleaned["subject"], cleaned["body"])
    final = combine(rules, ai_response)
    return render_template("result.html", data=cleaned, rules=rules, final=final)