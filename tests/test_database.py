import json
import sqlite3

import pytest

from app import database
from app.rules import analyze_rules
from app.scoring import combine


def save_sample(sender="a@example.com", subject="Hello", body="Hi there"):
    rules = analyze_rules(sender, subject, body)
    final = combine(rules, None)  # AI not available
    return database.save_scan(sender, subject, final, rules)


def test_save_and_get():
    scan_id = save_sample(subject="Test subject")
    scan = database.get_scan(scan_id)
    assert scan["subject"] == "Test subject"
    assert scan["category"] == "Low"
    assert isinstance(scan["findings"], dict)


def test_email_body_is_not_stored():
    scan_id = save_sample(body="my private note xyz123")
    scan = database.get_scan(scan_id)
    assert "xyz123" not in json.dumps(scan)


def test_list_is_newest_first():
    save_sample(subject="first")
    save_sample(subject="second")
    scans = database.list_scans()
    assert [s["subject"] for s in scans] == ["second", "first"]


def test_search_by_sender_and_subject():
    save_sample(sender="alice@example.com", subject="Invoice")
    save_sample(sender="bob@example.com", subject="Lunch")
    assert len(database.list_scans(search="alice")) == 1
    assert len(database.list_scans(search="Lunch")) == 1
    assert database.list_scans(search="nobody") == []


def test_category_filter():
    save_sample(subject="Lunch", body="Lunch at noon?")
    save_sample(
        sender="PayPal Support <help@paypa1-secure.xyz>",
        subject="Urgent: verify your account",
        body="Your account will be suspended. Act now and enter your password "
             "at http://192.168.4.7/login",
    )
    assert len(database.list_scans(category="Low")) == 1
    assert len(database.list_scans(category="High")) == 1


def test_sql_injection_text_is_treated_as_plain_text():
    save_sample()
    assert database.list_scans(search="'; DROP TABLE scans; --") == []
    assert len(database.list_scans()) == 1   # the table still exists


def test_delete_one_scan():
    keep = save_sample(subject="keep")
    remove = save_sample(subject="remove")
    database.delete_scan(remove)
    assert database.get_scan(remove) is None
    assert database.get_scan(keep) is not None


def test_clear_all():
    save_sample()
    save_sample()
    database.clear_scans()
    assert database.list_scans() == []


def test_missing_scan_returns_none():
    assert database.get_scan(9999) is None


def test_database_failure_raises_sqlite_error(tmp_path, monkeypatch):
    # Pointing the database at a folder (not a file) makes SQLite fail
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path))
    with pytest.raises(sqlite3.Error):
        database.list_scans()