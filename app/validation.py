import os

MAX_SENDER = 254
MAX_SUBJECT = 200
MAX_BODY = int(os.getenv("MAX_BODY_LENGTH", 10000))


def validate_email_input(sender, subject, body):
    """Trim the inputs and check them.
    Returns (cleaned_data, errors). If errors is empty, the input is valid."""
    cleaned = {
        "sender": (sender or "").strip(),
        "subject": (subject or "").strip(),
        "body": (body or "").strip(),
    }
    errors = {}

    if not cleaned["sender"]:
        errors["sender"] = "Sender is required."
    elif len(cleaned["sender"]) > MAX_SENDER:
        errors["sender"] = f"Sender must be at most {MAX_SENDER} characters."

    if not cleaned["subject"]:
        errors["subject"] = "Subject is required."
    elif len(cleaned["subject"]) > MAX_SUBJECT:
        errors["subject"] = f"Subject must be at most {MAX_SUBJECT} characters."

    if not cleaned["body"]:
        errors["body"] = "Email body is required."
    elif len(cleaned["body"]) > MAX_BODY:
        errors["body"] = f"Body must be at most {MAX_BODY} characters."

    return cleaned, errors