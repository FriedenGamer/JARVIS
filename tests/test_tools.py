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
    