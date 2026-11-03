import json

import pytest
import requests

from app import ollama_client
from app.ollama_client import analyze_with_ai, check_status, validate_ai_output


class FakeResponse:
    """A pretend response from Ollama."""

    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError("error")

    def json(self):
        return self._payload


GOOD_AI_JSON = {
    "verdict": "phishing",
    "risk_score": 90,
    "confidence": 0.85,
    "reasons": ["Asks for a password"],
    "evidence": ["enter your password"],
    "next_steps": ["Do not click the link"],
}


# ---------- validate_ai_output ----------

def test_valid_output_is_accepted():
    clean = validate_ai_output(GOOD_AI_JSON)
    assert clean["verdict"] == "phishing"
    assert clean["risk_score"] == 90


def test_numbers_are_clamped():
    data = dict(GOOD_AI_JSON, risk_score=500, confidence=7)
    clean = validate_ai_output(data)
    assert clean["risk_score"] == 100
    assert clean["confidence"] == 1.0


def test_invalid_verdict_rejected():
    with pytest.raises(ValueError):
        validate_ai_output(dict(GOOD_AI_JSON, verdict="maybe"))


def test_missing_score_rejected():
    data = {k: v for k, v in GOOD_AI_JSON.items() if k != "risk_score"}
    with pytest.raises(ValueError):
        validate_ai_output(data)


def test_non_dict_rejected():
    with pytest.raises(ValueError):
        validate_ai_output(["not", "a", "dict"])


# ---------- analyze_with_ai (mocked Ollama) ----------

def test_successful_analysis(monkeypatch):
    fake = FakeResponse({"response": json.dumps(GOOD_AI_JSON)})
    monkeypatch.setattr(ollama_client.requests, "post", lambda *a, **k: fake)
    result = analyze_with_ai("a@example.com", "Hi", "Hello")
    assert result["ok"] is True
    assert result["result"]["verdict"] == "phishing"


def test_invalid_json_from_model(monkeypatch):
    fake = FakeResponse({"response": "this is not json"})
    monkeypatch.setattr(ollama_client.requests, "post", lambda *a, **k: fake)
    result = analyze_with_ai("a@example.com", "Hi", "Hello")
    assert result["ok"] is False
    assert "invalid output" in result["error"]


def test_valid_json_but_wrong_fields(monkeypatch):
    fake = FakeResponse({"response": json.dumps({"verdict": "banana"})})
    monkeypatch.setattr(ollama_client.requests, "post", lambda *a, **k: fake)
    result = analyze_with_ai("a@example.com", "Hi", "Hello")
    assert result["ok"] is False


def test_timeout_is_handled(monkeypatch):
    def boom(*a, **k):
        raise requests.Timeout()
    monkeypatch.setattr(ollama_client.requests, "post", boom)
    result = analyze_with_ai("a@example.com", "Hi", "Hello")
    assert result["ok"] is False
    assert "timeout" in result["error"].lower()


def test_ollama_unavailable_is_handled(monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError()
    monkeypatch.setattr(ollama_client.requests, "post", boom)
    result = analyze_with_ai("a@example.com", "Hi", "Hello")
    assert result["ok"] is False
    assert "Cannot connect" in result["error"]


# ---------- check_status (mocked) ----------

def test_status_ollama_down(monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError()
    monkeypatch.setattr(ollama_client.requests, "get", boom)
    status = check_status()
    assert status["running"] is False


def test_status_model_missing(monkeypatch):
    fake = FakeResponse({"models": [{"name": "some-other-model:1b"}]})
    monkeypatch.setattr(ollama_client.requests, "get", lambda *a, **k: fake)
    status = check_status()
    assert status["running"] is True
    assert status["model_installed"] is False
    assert "ollama pull" in status["message"]