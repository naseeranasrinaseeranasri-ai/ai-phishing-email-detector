from app.rules import RuleResult, analyze_rules
from app.scoring import categorize, combine


def make_rules(score):
    return RuleResult(score=score, raw_score=score, indicators=[])


def ai_ok(risk_score):
    return {"ok": True, "result": {
        "verdict": "phishing", "risk_score": risk_score, "confidence": 0.8,
        "reasons": [], "evidence": [], "next_steps": [],
    }}


# ---------- Category thresholds ----------

def test_category_boundaries():
    assert categorize(0) == "Low"
    assert categorize(24) == "Low"
    assert categorize(25) == "Medium"
    assert categorize(49) == "Medium"
    assert categorize(50) == "High"
    assert categorize(74) == "High"
    assert categorize(75) == "Critical"
    assert categorize(100) == "Critical"


# ---------- Combining rules and AI ----------

def test_worked_example_from_documentation():
    # Rules 45 + AI 75 * 0.4 = 30  ->  75, Critical
    result = combine(make_rules(45), ai_ok(75))
    assert result["rule_points"] == 45
    assert result["ai_points"] == 30
    assert result["score"] == 75
    assert result["category"] == "Critical"


def test_ai_points_never_exceed_40():
    result = combine(make_rules(0), ai_ok(100))
    assert result["ai_points"] == 40


def test_final_score_clamped_to_100():
    result = combine(make_rules(60), ai_ok(100))
    assert result["score"] == 100


def test_ai_failure_falls_back_to_rules_only():
    result = combine(make_rules(35), {"ok": False, "error": "Cannot connect to Ollama."})
    assert result["ai_available"] is False
    assert result["score"] == 35
    assert result["ai_points"] == 0
    assert "Cannot connect" in result["ai_error"]
    assert "unavailable" in result["explanation"]


def test_none_ai_response_is_handled():
    result = combine(make_rules(10), None)
    assert result["ai_available"] is False
    assert result["score"] == 10


def test_legitimate_email_scores_low():
    rules = analyze_rules("friend@example.com", "Lunch?", "Lunch tomorrow at noon?")
    result = combine(rules, ai_ok(5))
    assert result["category"] == "Low"