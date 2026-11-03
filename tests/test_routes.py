import sqlite3

GOOD_AI = {"ok": True, "result": {
    "verdict": "phishing", "risk_score": 80, "confidence": 0.9,
    "reasons": ["Asks for a password"], "evidence": ["enter your password"],
    "next_steps": ["Do not click the link"],
}}
AI_DOWN = {"ok": False, "error": "Cannot connect to Ollama. Is it running?"}

SUSPICIOUS = {
    "sender": "PayPal Support <help@paypa1-secure.xyz>",
    "subject": "Urgent: verify your account",
    "body": "Your account will be suspended. Act now and enter your password "
            "at http://192.168.4.7/login",
}
NORMAL = {
    "sender": "friend@example.com",
    "subject": "Lunch tomorrow?",
    "body": "Want to grab lunch tomorrow at noon?",
}


def mock_ai(monkeypatch, response):
    monkeypatch.setattr("app.routes.analyze_with_ai", lambda *a, **k: response)


def test_home_page_loads(client):
    assert client.get("/").status_code == 200


def test_empty_form_is_rejected(client):
    resp = client.post("/analyze", data={"sender": "", "subject": "", "body": ""})
    assert resp.status_code == 400
    assert b"required" in resp.data


def test_whitespace_only_is_rejected(client):
    resp = client.post("/analyze", data={"sender": "  ", "subject": "  ", "body": "  "})
    assert resp.status_code == 400


def test_oversized_body_is_rejected(client):
    data = dict(NORMAL, body="a" * 20000)
    assert client.post("/analyze", data=data).status_code == 400


def test_suspicious_email_full_flow(client, monkeypatch):
    mock_ai(monkeypatch, GOOD_AI)
    resp = client.post("/analyze", data=SUSPICIOUS)
    assert resp.status_code == 200
    assert b"Critical" in resp.data or b"High" in resp.data
    assert b"advisory" in resp.data


def test_normal_email_scores_low(client, monkeypatch):
    mock_ai(monkeypatch, {"ok": True, "result": dict(GOOD_AI["result"],
            verdict="legitimate", risk_score=5, confidence=0.9)})
    resp = client.post("/analyze", data=NORMAL)
    assert b"(Low)" in resp.data


def test_ollama_down_still_shows_result(client, monkeypatch):
    mock_ai(monkeypatch, AI_DOWN)
    resp = client.post("/analyze", data=SUSPICIOUS)
    assert resp.status_code == 200
    assert b"AI analysis unavailable" in resp.data


def test_html_in_input_is_escaped(client, monkeypatch):
    mock_ai(monkeypatch, AI_DOWN)
    data = dict(NORMAL, subject="<script>alert(1)</script>")
    resp = client.post("/analyze", data=data)
    assert b"<script>alert(1)</script>" not in resp.data
    assert b"&lt;script&gt;" in resp.data


def test_database_failure_does_not_hide_result(client, monkeypatch):
    mock_ai(monkeypatch, GOOD_AI)

    def boom(*a, **k):
        raise sqlite3.OperationalError("disk error")
    monkeypatch.setattr("app.routes.database.save_scan", boom)

    resp = client.post("/analyze", data=SUSPICIOUS)
    assert resp.status_code == 200
    assert b"could not be saved" in resp.data


def test_scan_appears_in_history_and_detail(client, monkeypatch):
    mock_ai(monkeypatch, GOOD_AI)
    client.post("/analyze", data=SUSPICIOUS)
    assert b"Urgent: verify your account" in client.get("/history").data
    assert client.get("/history/1").status_code == 200
    assert client.get("/history/999").status_code == 404


def test_history_search_with_odd_text_does_not_crash(client):
    resp = client.get("/history", query_string={"q": "'; DROP TABLE scans; --"})
    assert resp.status_code == 200


def test_delete_scan(client, monkeypatch):
    mock_ai(monkeypatch, GOOD_AI)
    client.post("/analyze", data=SUSPICIOUS)
    client.post("/history/1/delete")
    assert client.get("/history/1").status_code == 404


def test_export_json(client, monkeypatch):
    mock_ai(monkeypatch, GOOD_AI)
    client.post("/analyze", data=SUSPICIOUS)
    resp = client.get("/history/1/export/json")
    assert resp.status_code == 200
    assert "attachment" in resp.headers["Content-Disposition"]
    report = resp.get_json()
    assert report["sender"] == SUSPICIOUS["sender"]
    assert "advisory" in report["disclaimer"]


def test_export_text(client, monkeypatch):
    mock_ai(monkeypatch, GOOD_AI)
    client.post("/analyze", data=SUSPICIOUS)
    resp = client.get("/history/1/export/txt")
    assert resp.status_code == 200
    assert b"PHISHING ANALYSIS REPORT" in resp.data


def test_export_unknown_format_or_scan(client, monkeypatch):
    mock_ai(monkeypatch, GOOD_AI)
    client.post("/analyze", data=SUSPICIOUS)
    assert client.get("/history/1/export/exe").status_code == 404
    assert client.get("/history/999/export/json").status_code == 404