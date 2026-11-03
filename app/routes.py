import sqlite3

from flask import Blueprint, Response, abort, jsonify, redirect, render_template, request, url_for

from . import database
from .ollama_client import analyze_with_ai, check_status
from .reports import build_json_report, build_text_report
from .rules import analyze_rules
from .scoring import combine
from .validation import validate_email_input

import logging

logger = logging.getLogger(__name__)

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html", values={}, errors={})

@main.route("/status")
def status():
    return jsonify(check_status())


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

    # A database problem must not hide the analysis from the user
    scan_id, save_error = None, None
    try:
        scan_id = database.save_scan(cleaned["sender"], cleaned["subject"], final, rules)
        logger.info("Scan saved: id=%s score=%s category=%s ai_available=%s",
                    scan_id, final["score"], final["category"], final["ai_available"])
    except sqlite3.Error as exc:
        logger.error("Could not save scan: %s", type(exc).__name__)
        save_error = "The scan could not be saved to history."

    return render_template("result.html", data=cleaned, rules=rules, final=final,
                           scan_id=scan_id, save_error=save_error)


@main.route("/history")
def history():
    search = request.args.get("q", "").strip()[:100]
    category = request.args.get("category", "").strip()
    if category not in {"Low", "Medium", "High", "Critical"}:
        category = ""
    try:
        scans = database.list_scans(search, category)
        error = None
    except sqlite3.Error:
        scans, error = [], "History could not be loaded."
    return render_template("history.html", scans=scans, search=search,
                           category=category, error=error)


@main.route("/history/<int:scan_id>")
def scan_detail(scan_id):
    scan = database.get_scan(scan_id)
    if scan is None:
        abort(404)
    return render_template("detail.html", scan=scan)


@main.route("/history/<int:scan_id>/export/<fmt>")
def export_scan(scan_id, fmt):
    if fmt not in ("json", "txt"):
        abort(404)
    scan = database.get_scan(scan_id)
    if scan is None:
        abort(404)
    if fmt == "json":
        body, mimetype = build_json_report(scan), "application/json"
    else:
        body, mimetype = build_text_report(scan), "text/plain"
    return Response(
        body,
        mimetype=mimetype,
        headers={"Content-Disposition": f"attachment; filename=scan-{scan_id}.{fmt}"},
    )


@main.route("/history/<int:scan_id>/delete", methods=["POST"])
def delete_scan(scan_id):
    database.delete_scan(scan_id)
    return redirect(url_for("main.history"))


@main.route("/history/clear", methods=["POST"])
def clear_history():
    database.clear_scans()
    return redirect(url_for("main.history"))