import tools


def test_read_inbox_returns_six_emails():
    result = tools.read_inbox()
    assert result["success"] is True
    assert result["error"] is None
    assert len(result["data"]) == 6


def test_get_bill_details_finds_bill():
    result = tools.get_bill_details("e1")
    assert result["success"] is True
    assert result["data"]["id"] == "b1"
    assert result["data"]["amount"] == 1850


def test_get_bill_details_bill_not_found():
    result = tools.get_bill_details("e99")
    assert result["success"] is False
    assert result["data"] is None
    assert result["error"] == "Bill not found"


def test_plan_week_sorted_by_due_date():
    result = tools.plan_week()
    assert result["success"] is True
    ids = [task["id"] for task in result["data"]]
    assert ids == ["t2", "t1", "t4", "t3", "t5", "t6"]

def test_view_calendar_busy_slot():
    result = tools.view_calendar("2026-11-27")
    assert result["success"] is True
    assert "Team sync" in str(result["data"])


def test_add_reminder_empty_title_fails():
    result = tools.add_reminder("", "2026-11-30")
    assert result["success"] is False
    assert "title cannot be empty" in str(result["error"])


def test_add_reminder_duplicate_skipped():
    first = tools.add_reminder("Submit demo", "2026-12-02")
    second = tools.add_reminder("Submit demo", "2026-12-02")
    assert first["success"] is True
    assert second["success"] is True
    assert second["data"].get("skipped_duplicate") is True


def test_draft_email_returns_draft_data():
    result = tools.draft_email("judge@example.com", "Demo Invite", "Join at 3 PM.")
    assert result["success"] is True
    assert result["data"] is not None


def test_book_appointment_busy_slot_fails():
    result = tools.book_appointment("Clash meeting", "2026-11-27", "11:00")
    assert result["success"] is False
    assert "Slot is busy" in str(result["error"])


def test_pay_bill_wrong_amount_fails():
    result = tools.pay_bill("b1", 1000)
    assert result["success"] is False
    assert "Amount does not match bill amount" in str(result["error"])


def test_pay_bill_double_pay_fails():
    first = tools.pay_bill("b1", 1850)
    second = tools.pay_bill("b1", 1850)
    assert first["success"] is True
    assert second["success"] is False
    assert "Bill already paid" in str(second["error"])


def test_pay_bill_wallet_too_small_fails():
    first = tools.pay_bill("b1", 1850)
    second = tools.pay_bill("b2", 999)
    assert first["success"] is True
    assert second["success"] is False
    assert "Insufficient wallet balance" in str(second["error"])


def test_fill_form_unknown_form_fails():
    result = tools.fill_form("missing_form", {"name": "Shiva"})
    assert result["success"] is False
    assert "Form not found" in str(result["error"])


def test_calculate_divide_by_zero_fails():
    result = tools.calculate("10 / 0")
    assert result["success"] is False
    assert result["error"] is not None

def test_calculate_valid_expression_succeeds():
    result = tools.calculate("25 * 4 + 10")
    assert result["success"] is True
    assert result["data"]["expression"] == "25 * 4 + 10"
    assert result["data"]["result"] == 110
    assert result["error"] is None


def test_read_inbox_succeeds():
    result = tools.read_inbox()
    assert result["success"] is True
    assert result["data"] is not None
    assert result["error"] is None


def test_get_bill_details_missing_email_id_fails():
    result = tools.get_bill_details("b1")
    assert result["success"] is False
    assert "Bill not found" in str(result["error"])


def test_plan_week_succeeds():
    result = tools.plan_week()
    assert result["success"] is True
    assert result["data"] is not None
    assert result["error"] is None


def test_get_current_time_succeeds():
    result = tools.get_current_time()
    assert result["success"] is True
    assert isinstance(result["data"], dict)
    assert {"date", "time", "iso"}.issubset(result["data"].keys())
    assert result["error"] is None
