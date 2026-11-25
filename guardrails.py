import json
import db
from datetime import datetime

RISK = {
    "read_inbox": "low",
    "get_bill_details": "low",
    "add_reminder": "low",
    "plan_week": "low",
    "view_calendar": "low",
    "calculate": "low",
    "get_current_time": "low",
    "draft_email": "high",
    "pay_bill": "high",
    "book_appointment": "high",
    "fill_form": "high",
}


def get_risk(tool):
    """Return 'low' or 'high'. Unknown tools are not allowed at all."""
    if tool not in RISK:
        return None
    return RISK[tool]


def load_json(name):
    """Read one seed file from the data folder."""
    with open("data/" + name, "r") as f:
        return json.load(f)


def is_real_date(value):
    """True only for a real date like 2026-12-05."""
    try:
        datetime.strptime(str(value), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def is_real_time(value):
    """True only for a real time like 10:30."""
    try:
        datetime.strptime(str(value), "%H:%M")
        return True
    except ValueError:
        return False


def validate_call(tool, args):
    """Check the AI's arguments. Return (True, None) or (False, 'reason')."""
    if get_risk(tool) is None:
        return False, "Tool not allowed: " + str(tool)

    if tool == "add_reminder":
        if str(args.get("title", "")).strip() == "":
            return False, "Title is empty."
        if not is_real_date(args.get("due_date")):
            return False, "Date must be a real date like 2026-12-05."

    if tool == "draft_email":
        for field in ["to", "subject", "body"]:
            if str(args.get(field, "")).strip() == "":
                return False, "Email is missing: " + field

    if tool == "get_bill_details":
        ids = [e["id"] for e in load_json("emails.json")]
        if args.get("email_id") not in ids:
            return False, "Email not found."

    if tool == "pay_bill":
        bills = load_json("bills.json")
        bill = None
        for b in bills:
            if b["id"] == args.get("bill_id"):
                bill = b
        if bill is None:
            return False, "Bill not found."
        try:
            amount = float(args.get("amount"))
        except (TypeError, ValueError):
            return False, "Amount must be a number."
        if amount != float(bill["amount"]):
            return False, "Amount must be exactly Rs " + str(bill["amount"])
        payments = [
            r["data"] for r in db.list_records("payment")
            if isinstance(r.get("data"), dict)
        ]
        for p in payments:
            if p.get("bill_id") == args.get("bill_id"):
                return False, "Bill already paid."

        wallet = load_json("wallet.json")
        spent = sum(p.get("amount", 0) for p in payments)
        balance = wallet.get("starting_balance", 0) - spent
        if amount > balance:
            return False, "Not enough money in the wallet. Balance is Rs " + str(balance)

    if tool == "view_calendar":
        if not is_real_date(args.get("date")):
            return False, "Date must be a real date like 2026-12-05."

    if tool == "book_appointment":
        if str(args.get("title", "")).strip() == "":
            return False, "Title is empty."
        if not is_real_date(args.get("date")):
            return False, "Date must be a real date like 2026-12-05."
        if not is_real_time(args.get("time")):
            return False, "Time must look like 10:30."
        date_val = str(args.get("date"))
        time_val = str(args.get("time"))
        for day in load_json("calendar.json"):
            if day.get("date") == date_val:
                for slot in day.get("slots", []):
                    if slot.get("time") == time_val and slot.get("status") == "busy":
                        return False, "Slot is busy."

        bookings = [
            r["data"] for r in db.list_records("booking")
            if isinstance(r.get("data"), dict)
        ]
        for b in bookings:
            if b.get("date") == date_val and b.get("time") == time_val:
                return False, "Slot is already booked."

    if tool == "fill_form":
        if str(args.get("form_name", "")).strip() == "":
            return False, "Form name is empty."
        if not isinstance(args.get("fields"), dict):
            return False, "Fields must be a list of name and value pairs."

        form = None
        for f in load_json("forms.json"):
            if f["form_name"] == args.get("form_name"):
                form = f
        if form is None:
            return False, "Form not found: " + str(args.get("form_name"))

        for field in args["fields"]:
            if field not in form["fields"]:
                return False, "Unknown field: " + str(field)

    if tool == "calculate":
        expression = str(args.get("expression", "")).strip()
        if expression == "":
            return False, "Expression is empty."
        for ch in expression:
            if ch not in "0123456789+-*/(). ":
                return False, "Only numbers and + - * / ( ) are allowed."

    return True, None