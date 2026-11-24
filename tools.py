import ast
from datetime import datetime
import json
import operator
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REMINDERS = []
DRAFTS = []
BOOKINGS = []
PAYMENTS = []
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}

_SAFE_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_SAFE_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _ok(data):
    return {"success": True, "data": data, "error": None}


def _fail(error):
    return {"success": False, "data": None, "error": error}


def _load_json(filename):
    path = BASE_DIR / "data" / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _valid_date(date_str):
    if not isinstance(date_str, str):
        return False
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
        return parsed.strftime("%Y-%m-%d") == date_str
    except ValueError:
        return False


def _valid_time(time_str):
    if not isinstance(time_str, str):
        return False
    try:
        parsed = datetime.strptime(time_str, "%H:%M")
        return parsed.strftime("%H:%M") == time_str
    except ValueError:
        return False


def _eval_math_node(node):
    if isinstance(node, ast.Expression):
        return _eval_math_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_UNARYOPS:
        return _SAFE_UNARYOPS[type(node.op)](_eval_math_node(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_BINOPS:
        left = _eval_math_node(node.left)
        right = _eval_math_node(node.right)
        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)) and right == 0:
            raise ZeroDivisionError("Division by zero")
        return _SAFE_BINOPS[type(node.op)](left, right)
    raise ValueError("Unsafe or unsupported math expression")


def read_inbox():
    try:
        return _ok(_load_json("emails.json"))
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
        return _fail("title cannot be empty")
    if not _valid_date(due_date):
        return _fail("due_date must be a valid YYYY-MM-DD date")

    clean_title = title.strip()
    for item in REMINDERS:
        if item["title"].lower() == clean_title.lower() and item["due_date"] == due_date:
            return _fail("Duplicate reminder")

    reminder = {"title": clean_title, "due_date": due_date}
    REMINDERS.append(reminder)
    return _ok(reminder)


def plan_week():
    try:
        tasks = _load_json("tasks.json")
        ordered = sorted(
            tasks,
            key=lambda t: (
                t.get("due_date", "9999-12-31"),
                PRIORITY_RANK.get(str(t.get("priority", "low")).lower(), 99),
                str(t.get("id", "")),
            ),
        )
        return _ok(ordered)
    except Exception as exc:
        return _fail(str(exc))


def draft_email(to, subject, body):
    if not isinstance(to, str) or not to.strip():
        return _fail("to cannot be empty")
    if not isinstance(subject, str) or not subject.strip():
        return _fail("subject cannot be empty")
    if not isinstance(body, str) or not body.strip():
        return _fail("body cannot be empty")

    draft = {
        "to": to.strip(),
        "subject": subject.strip(),
        "body": body.strip(),
        "status": "draft",
    }
    DRAFTS.append(draft)
    return _ok(draft)


def view_calendar(date):
    if not _valid_date(date):
        return _fail("date must be a valid YYYY-MM-DD date")
    try:
        entries = _load_json("calendar.json")
        for entry in entries:
            if entry.get("date") == date:
                return _ok({"date": date, "slots": entry.get("slots", [])})
        return _ok({"date": date, "slots": []})
    except Exception as exc:
        return _fail(str(exc))


def book_appointment(title, date, time):
    if not isinstance(title, str) or not title.strip():
        return _fail("title cannot be empty")
    if not _valid_date(date):
        return _fail("date must be a valid YYYY-MM-DD date")
    if not _valid_time(time):
        return _fail("time must be a valid HH:MM time")

    try:
        entries = _load_json("calendar.json")
        for entry in entries:
            if entry.get("date") == date:
                for slot in entry.get("slots", []):
                    if slot.get("time") == time and slot.get("status") == "busy":
                        return _fail("Slot is busy")

        clean_title = title.strip()
        for existing in BOOKINGS:
            if existing["date"] == date and existing["time"] == time:
                return _fail("Slot is busy")

        booking = {
            "title": clean_title,
            "date": date,
            "time": time,
            "status": "booked",
        }
        BOOKINGS.append(booking)
        return _ok(booking)
    except Exception as exc:
        return _fail(str(exc))


def pay_bill(bill_id, amount):
    try:
        bills = _load_json("bills.json")
        wallet = _load_json("wallet.json")

        target_bill = None
        for bill in bills:
            if bill.get("id") == bill_id:
                target_bill = bill
                break

        if target_bill is None:
            return _fail("Bill not found")

        for payment in PAYMENTS:
            if payment.get("bill_id") == bill_id:
                return _fail("Bill already paid")

        expected_amount = target_bill.get("amount")
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount != expected_amount:
            return _fail("Amount does not match bill amount")

        starting_balance = wallet.get("starting_balance", 0)
        spent = sum(p.get("amount", 0) for p in PAYMENTS)
        available_balance = starting_balance - spent

        if amount > available_balance:
            return _fail("Insufficient wallet balance")

        payment = {
            "bill_id": bill_id,
            "vendor": target_bill.get("vendor"),
            "amount": amount,
            "simulated": True,
            "status": "paid",
        }
        PAYMENTS.append(payment)
        return _ok(payment)
    except Exception as exc:
        return _fail(str(exc))


def calculate(expression):
    if not isinstance(expression, str) or not expression.strip():
        return _fail("expression cannot be empty")
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _eval_math_node(tree)
        return _ok({"expression": expression.strip(), "result": result})
    except Exception as exc:
        return _fail(str(exc))


def get_current_time():
    now = datetime.now()
    return _ok(
        {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "iso": now.isoformat(),
        }
    )


def fill_form(form_name, fields):
    if not isinstance(form_name, str) or not form_name.strip():
        return _fail("form_name cannot be empty")
    if not isinstance(fields, dict) or not fields:
        return _fail("fields must be a non-empty dictionary")

    try:
        templates = _load_json("forms.json")
        allowed_fields = None
        clean_name = form_name.strip()

        if isinstance(templates, list):
            for item in templates:
                if isinstance(item, dict) and item.get("form_name") == clean_name:
                    raw_fields = item.get("fields", [])
                    if isinstance(raw_fields, list):
                        allowed_fields = {f for f in raw_fields if isinstance(f, str)}
                    break
        elif isinstance(templates, dict):
            entry = templates.get(clean_name)
            if isinstance(entry, dict) and isinstance(entry.get("fields"), list):
                allowed_fields = {f for f in entry["fields"] if isinstance(f, str)}
            elif isinstance(entry, list):
                allowed_fields = {f for f in entry if isinstance(f, str)}

        if allowed_fields is None:
            return _fail("Form not found")

        unknown_keys = [k for k in fields.keys() if k not in allowed_fields]
        if unknown_keys:
            return _fail(f"Unknown or unallowed fields: {', '.join(unknown_keys)}")

        return _ok(
            {
                "form_name": clean_name,
                "fields": fields,
                "status": "filled",
            }
        )
    except Exception as exc:
        return _fail(str(exc))