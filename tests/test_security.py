import logging

AI_DOWN = {"ok": False, "error": "Cannot connect to Ollama. Is it running?"}
EMAIL = {
    "sender": "PayPal Support <help@paypa1-secure.xyz>",
    "subject": "Urgent: verify your account",
    "body": "Act now at http://192.168.4.7/login",
}


def test_security_headers_present(client):
    resp = client.get("/")
    assert "default-src 'self'" in resp.headers["Content-Security-Policy"]
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"


def test_huge_request_is_rejected(client):
    data = {"sender": "a@example.com", "subject": "x", "body": "a" * 300000}
    assert client.post("/analyze", data=data).status_code == 413


def test_no_inline_scripts_in_history_page(client):
    html = client.get("/history").data
    assert b"onsubmit=" not in html
    assert b"onclick=" not in html


def test_logs_do_not_contain_email_content(client, monkeypatch, caplog):
    monkeypatch.setattr("app.routes.analyze_with_ai", lambda *a, **k: AI_DOWN)
    caplog.set_level(logging.INFO)
    client.post("/analyze", data=EMAIL)
    assert "Scan saved" in caplog.text
    assert "paypa1" not in caplog.text
    assert "192.168" not in caplog.text