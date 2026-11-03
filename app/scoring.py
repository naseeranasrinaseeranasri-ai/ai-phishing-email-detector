MAX_AI_POINTS = 40

CATEGORIES = [
    (75, "Critical"),
    (50, "High"),
    (25, "Medium"),
    (0, "Low"),
]


def categorize(score):
    for threshold, name in CATEGORIES:
        if score >= threshold:
            return name
    return "Low"


def combine(rule_result, ai_response):
    """Combine rule results and the AI response into one final result.

    rule_result: RuleResult from rules.py
    ai_response: dict from analyze_with_ai ({"ok": ..., "result" or "error": ...})
    """
    rule_points = rule_result.score
    ai_available = bool(ai_response and ai_response.get("ok"))

    if ai_available:
        ai = ai_response["result"]
        ai_points = round(ai["risk_score"] * MAX_AI_POINTS / 100)
    else:
        ai = None
        ai_points = 0

    final = max(0, min(100, rule_points + ai_points))

    return {
        "score": final,
        "category": categorize(final),
        "rule_points": rule_points,
        "ai_points": ai_points,
        "ai_available": ai_available,
        "ai_error": None if ai_available else (ai_response or {}).get("error", "AI not run."),
        "ai": ai,
        "explanation": _explain(rule_points, ai_points, ai_available),
    }


def _explain(rule_points, ai_points, ai_available):
    if ai_available:
        return (f"Rule checks added {rule_points} points (max 60) and the AI assessment "
                f"added {ai_points} points (max 40).")
    return (f"Rule checks added {rule_points} points (max 60). The AI analysis was "
            "unavailable, so this score is based on rules only and may miss risks.")