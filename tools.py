from datetime import datetime
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REMINDERS = []
DRAFTS = []
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def _ok(data):
    return {"success": True, "data": data, "error": None}


def _fail(error):
    return {"success": False, "data": None, "error": error}


def _load_json(filename):
    path = BASE_DIR / "data" / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _valid_date(due_date):
    if not isinstance(due_date, str):
        return False
    try:
        parsed = datetime.strptime(due_date, "%Y-%m-%d")
        return parsed.strftime("%Y-%m-%d") == due_date
    except ValueError:
        return False


def read_inbox():
    try:
        emails = _load_json("emails.json")
        return _ok(emails)
    except Exception as exc:
        return _fail(str(exc))


def get_bill_details(email_id):
    try:
        bills = _load_json("bills.json")
        for bill in bills:
            if bill.get("email_id") == email_id:
                return _ok(bill)
        return _fail("Bill not found")
    except Exception as exc:
        return _fail(str(exc))


def add_reminder(title, due_date):
    if not isinstance(title, str) or not title.strip():
        return _fail("Title cannot be empty")
    if not _valid_date(due_date):
        return _fail("due_date must be YYYY-MM-DD")

    clean_title = title.strip()
    for item in REMINDERS:
        if item["title"] == clean_title and item["due_date"] == due_date:
            return _fail("Duplicate reminder")

    reminder = {"title": clean_title, "due_date": due_date}
    REMINDERS.append(reminder)
    return _ok(reminder)


def plan_week():
    try:
        tasks = _load_json("tasks.json")
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (
                t.get("due_date", ""),
                PRIORITY_RANK.get(t.get("priority", "low"), 99),
                str(t.get("id", "")),
            ),
        )
        return _ok(sorted_tasks)
    except Exception as exc:
        return _fail(str(exc))


def draft_email(to, subject, body):
    if not isinstance(to, str) or not to.strip():
        return _fail("Recipient 'to' is required")
    if not isinstance(subject, str) or not subject.strip():
        return _fail("Subject is required")
    if not isinstance(body, str) or not body.strip():
        return _fail("Body is required")

    draft = {
        "to": to.strip(),
        "subject": subject.strip(),
        "body": body.strip(),
        "status": "draft",
    }
    DRAFTS.append(draft)
    return _ok(draft)