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