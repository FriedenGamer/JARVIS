from datetime import datetime

RISK = {
    "read_inbox": "low",
    "get_bill_details": "low",
    "add_reminder": "low",
    "plan_week": "low",
    "draft_email": "high",
}


def get_risk(tool):
    """Return 'low' or 'high'. Unknown tools are not allowed at all."""
    if tool not in RISK:
        return None
    return RISK[tool]


def validate_call(tool, args):
    """Check the AI's arguments. Return (True, None) or (False, 'reason')."""
    if get_risk(tool) is None:
        return False, "Tool not allowed: " + str(tool)

    if tool == "add_reminder":
        title = str(args.get("title", "")).strip()
        if title == "":
            return False, "Title is empty."
        try:
            datetime.strptime(str(args.get("due_date", "")), "%Y-%m-%d")
        except ValueError:
            return False, "Date must be a real date like 2026-12-05."

    if tool == "draft_email":
        for field in ["to", "subject", "body"]:
            if str(args.get(field, "")).strip() == "":
                return False, "Email is missing: " + field

    return True, None