import json

DISCLAIMER = ("This result is advisory only. It is not a guarantee that an email "
              "is safe or malicious.")


def build_json_report(scan):
    report = {
        "scan_id": scan["id"],
        "created_at_utc": scan["created_at"],
        "sender": scan["sender"],
        "subject": scan["subject"],
        "score": scan["score"],
        "category": scan["category"],
        "findings": scan["findings"],
        "disclaimer": DISCLAIMER,
    }
    return json.dumps(report, indent=2, ensure_ascii=False)


def build_text_report(scan):
    f = scan["findings"]
    lines = [
        f"PHISHING ANALYSIS REPORT - Scan #{scan['id']}",
        f"Time (UTC): {scan['created_at']}",
        f"Sender: {scan['sender']}",
        f"Subject: {scan['subject']}",
        f"Risk score: {scan['score']} / 100 ({scan['category']})",
        f.get("explanation", ""),
        "",
        f"RULE INDICATORS ({f.get('rule_points', 0)} / 60)",
    ]
    indicators = f.get("indicators", [])
    if not indicators:
        lines.append("  None found.")
    for ind in indicators:
        lines.append(f"  - {ind['name']} (+{ind['points']}): {ind['explanation']}")
        for e in ind.get("evidence", []):
            lines.append(f"      evidence: {e}")

    lines += ["", f"AI ASSESSMENT ({f.get('ai_points', 0)} / 40)"]
    ai = f.get("ai")
    if ai:
        lines.append(f"  Verdict: {ai['verdict']} | Confidence: {round(ai['confidence'] * 100)}%")
        for title, key in (("Reasons", "reasons"), ("Evidence", "evidence"),
                           ("Next steps", "next_steps")):
            lines.append(f"  {title}:")
            lines += [f"    - {item}" for item in ai.get(key, [])]
    else:
        lines.append(f"  Unavailable: {f.get('ai_error', '')}")

    lines += ["", DISCLAIMER]
    return "\n".join(lines)