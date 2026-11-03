import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT    NOT NULL,
    sender     TEXT    NOT NULL,
    subject    TEXT    NOT NULL,
    score      INTEGER NOT NULL,
    category   TEXT    NOT NULL,
    findings   TEXT    NOT NULL
);
"""


def _db_path():
    path = Path(os.getenv("DATABASE_PATH", "instance/scans.db"))
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _connect():
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(_connect()) as conn:
        conn.execute(SCHEMA)
        conn.commit()


def save_scan(sender, subject, final, rules):
    """Save one scan. Returns the new scan id."""
    findings = {
        "explanation": final["explanation"],
        "rule_points": final["rule_points"],
        "ai_points": final["ai_points"],
        "ai_available": final["ai_available"],
        "ai_error": final["ai_error"],
        "indicators": [
            {"name": i.name, "points": i.points,
             "explanation": i.explanation, "evidence": i.evidence}
            for i in rules.indicators
        ],
        "ai": final["ai"],
    }
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with closing(_connect()) as conn:
        cur = conn.execute(
            "INSERT INTO scans (created_at, sender, subject, score, category, findings) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (created_at, sender, subject, final["score"], final["category"],
             json.dumps(findings)),
        )
        conn.commit()
        return cur.lastrowid


def list_scans(search="", category=""):
    query = "SELECT id, created_at, sender, subject, score, category FROM scans WHERE 1=1"
    params = []
    if search:
        query += " AND (sender LIKE ? OR subject LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    if category:
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY id DESC LIMIT 200"
    with closing(_connect()) as conn:
        return [dict(row) for row in conn.execute(query, params).fetchall()]


def get_scan(scan_id):
    with closing(_connect()) as conn:
        row = conn.execute("SELECT * FROM scans WHERE id = ?", (scan_id,)).fetchone()
    if row is None:
        return None
    scan = dict(row)
    try:
        scan["findings"] = json.loads(scan["findings"])
    except ValueError:
        scan["findings"] = {}
    return scan


def delete_scan(scan_id):
    with closing(_connect()) as conn:
        conn.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
        conn.commit()


def clear_scans():
    with closing(_connect()) as conn:
        conn.execute("DELETE FROM scans")
        conn.commit()