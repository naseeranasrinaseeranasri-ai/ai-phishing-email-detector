import re
from dataclasses import dataclass, field
from email.utils import parseaddr
from urllib.parse import urlparse

MAX_RULE_SCORE = 60

URGENCY_PHRASES = [
    "act now", "immediately", "urgent", "right away", "as soon as possible",
    "within 24 hours", "within 48 hours", "final notice", "last warning",
    "expires today", "limited time",
]
THREAT_PHRASES = [
    "account will be suspended", "account will be closed", "account has been suspended",
    "account will be locked", "legal action", "permanently disabled",
    "unauthorized activity", "suspicious activity", "will be terminated",
]
CREDENTIAL_PHRASES = [
    "verify your password", "confirm your password", "enter your password",
    "your password", "one-time password", "otp", "verification code",
    "login credentials", "security code", "pin number", "social security",
    "confirm your identity", "verify your account",
]
PAYMENT_PHRASES = [
    "gift card", "wire transfer", "bank transfer", "update your payment",
    "payment details", "credit card number", "card number", "bitcoin",
    "pay the invoice", "billing information",
]

URL_SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "cutt.ly", "rb.gy"}
RISKY_ENDINGS = (".xyz", ".top", ".click", ".zip", ".work", ".support", ".tk", ".gq")

# Brand name -> real domains that brand uses
BRAND_DOMAINS = {
    "paypal": ["paypal.com"],
    "microsoft": ["microsoft.com", "outlook.com", "office.com"],
    "amazon": ["amazon.com"],
    "google": ["google.com", "gmail.com"],
    "apple": ["apple.com", "icloud.com"],
    "netflix": ["netflix.com"],
}

URL_PATTERN = re.compile(r"(?:https?://|www\.)[^\s<>\"']+", re.IGNORECASE)
IP_PATTERN = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


@dataclass
class Indicator:
    name: str
    points: int
    explanation: str
    evidence: list = field(default_factory=list)


@dataclass
class RuleResult:
    score: int                 # capped at MAX_RULE_SCORE
    raw_score: int             # before the cap
    indicators: list = field(default_factory=list)


def _matches(text, phrases):
    """Return the phrases found in text as whole words (text must be lowercase)."""
    found = []
    for phrase in phrases:
        if re.search(r"\b" + re.escape(phrase) + r"\b", text):
            found.append(phrase)
    return found


def check_urgency(text):
    found = _matches(text.lower(), URGENCY_PHRASES)
    if not found:
        return None
    return Indicator("Urgent language", 10,
                     "Pressure to act quickly is a common phishing tactic.", found)


def check_threats(text):
    found = _matches(text.lower(), THREAT_PHRASES)
    if not found:
        return None
    return Indicator("Threatening language", 10,
                     "Threats of account loss or legal action are used to cause panic.", found)


def check_credentials(text):
    found = _matches(text.lower(), CREDENTIAL_PHRASES)
    if not found:
        return None
    return Indicator("Credential request", 20,
                     "Legitimate companies rarely ask for passwords or codes by email.", found)


def check_payment(text):
    found = _matches(text.lower(), PAYMENT_PHRASES)
    if not found:
        return None
    return Indicator("Payment request", 15,
                     "Requests for payment details or unusual payment methods are risky.", found)


def check_urls(text):
    """Look at link text only. We NEVER open or visit any link."""
    evidence = []
    for url in URL_PATTERN.findall(text):
        url = url.rstrip(".,;:!?)")
        parsed = urlparse(url if url.lower().startswith("http") else "http://" + url)
        host = (parsed.hostname or "").lower()
        if not host:
            continue
        if IP_PATTERN.match(host):
            evidence.append(f"{url} (IP address instead of a domain name)")
        elif host in URL_SHORTENERS:
            evidence.append(f"{url} (URL shortener hides the real destination)")
        elif host.endswith(RISKY_ENDINGS):
            evidence.append(f"{url} (domain ending often used in abuse)")
        elif "xn--" in host:
            evidence.append(f"{url} (look-alike characters in domain)")
        elif "@" in parsed.netloc:
            evidence.append(f"{url} (contains @ to disguise the real host)")
    if not evidence:
        return None
    return Indicator("Suspicious URL", 15,
                     "Links that hide or disguise their destination are a red flag.", evidence)


def check_sender_mismatch(sender):
    """Display name claims a brand, but the email domain is not that brand's."""
    display_name, address = parseaddr(sender)
    if not display_name or "@" not in address:
        return None  # not enough data, so no signal
    domain = address.rsplit("@", 1)[1].lower()
    for brand, real_domains in BRAND_DOMAINS.items():
        if brand in display_name.lower():
            ok = any(domain == d or domain.endswith("." + d) for d in real_domains)
            if not ok:
                return Indicator(
                    "Sender mismatch", 15,
                    "The display name claims a brand, but the email domain does not belong to it.",
                    [f'Display name "{display_name}" but domain is "{domain}"'])
    return None


def analyze_rules(sender, subject, body):
    """Run every check once and combine the results."""
    text = f"{subject}\n{body}"
    checks = [
        check_urgency(text),
        check_threats(text),
        check_credentials(text),
        check_payment(text),
        check_urls(text),
        check_sender_mismatch(sender),
    ]
    indicators = [c for c in checks if c is not None]
    raw = sum(i.points for i in indicators)
    return RuleResult(score=min(raw, MAX_RULE_SCORE), raw_score=raw, indicators=indicators)