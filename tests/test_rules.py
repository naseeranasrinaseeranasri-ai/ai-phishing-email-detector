from app.rules import (
    analyze_rules,
    check_credentials,
    check_payment,
    check_sender_mismatch,
    check_threats,
    check_urgency,
    check_urls,
)

# All examples below are synthetic.


# ---------- Individual indicators ----------

def test_urgency_detected():
    result = check_urgency("Act now or your account will be closed")
    assert result is not None
    assert result.points == 10
    assert "act now" in result.evidence


def test_urgency_not_detected_in_normal_text():
    assert check_urgency("Want to grab lunch tomorrow?") is None


def test_threats_detected():
    result = check_threats("Your account will be suspended today")
    assert result is not None
    assert result.points == 10


def test_credential_request_detected():
    result = check_credentials("Please enter your password to continue")
    assert result is not None
    assert result.points == 20


def test_payment_request_detected():
    result = check_payment("Please buy a gift card and send the code")
    assert result is not None
    assert result.points == 15


def test_url_with_ip_address_detected():
    result = check_urls("Log in at http://192.168.4.7/login")
    assert result is not None
    assert result.points == 15


def test_url_shortener_detected():
    result = check_urls("Click http://bit.ly/abc123")
    assert result is not None


def test_normal_url_not_flagged():
    assert check_urls("Read more at https://www.example.com/page") is None


def test_sender_mismatch_detected():
    result = check_sender_mismatch("PayPal Support <help@paypa1-secure.xyz>")
    assert result is not None
    assert result.points == 15


def test_real_brand_domain_not_flagged():
    assert check_sender_mismatch("PayPal <service@paypal.com>") is None


def test_plain_address_gives_no_mismatch_signal():
    assert check_sender_mismatch("friend@example.com") is None


# ---------- Combined analysis ----------

def test_repeated_phrases_count_only_once():
    result = analyze_rules(
        "friend@example.com",
        "Hi",
        "urgent urgent urgent, act now, immediately",
    )
    urgency = [i for i in result.indicators if i.name == "Urgent language"]
    assert len(urgency) == 1
    assert result.score == 10


def test_score_is_capped_at_60():
    result = analyze_rules(
        "PayPal Support <help@paypa1-secure.xyz>",
        "Urgent: verify your account",
        "Your account will be suspended. Act now and enter your password "
        "at http://192.168.4.7/login or http://bit.ly/abc123",
    )
    assert result.raw_score > 60
    assert result.score == 60


def test_normal_email_scores_zero():
    result = analyze_rules(
        "friend@example.com",
        "Lunch tomorrow?",
        "Want to grab lunch tomorrow at noon?",
    )
    assert result.score == 0
    assert result.indicators == []