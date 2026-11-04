"""貸出と返却の業務処理を確かめる（既に貸出中、返却済み、借りる社員、未来の日付）。"""

import pytest

from app import accounts, equipment, loans
from app.errors import RuleViolation


@pytest.fixture
def setup_data(conn):
    accounts.register_account(conn, "100001", "山田", "password1")
    accounts.register_account(conn, "100002", "佐藤", "password2")
    equipment.create_equipment(conn, "EQ-1", "椅子")
    return conn


def test_lend_then_return(setup_data):
    conn = setup_data
    loans.lend_equipment(conn, "EQ-1", 1, "100002", "2026-11-03", today="2026-11-04")
    row = equipment.list_lending_status(conn)[0]
    assert (row["borrower_name"], row["lent_on"]) == ("佐藤", "2026-11-03")
    loans.return_equipment(conn, "EQ-1", 1)
    assert equipment.list_lending_status(conn)[0]["lent_on"] is None


def test_lend_twice_is_rejected(setup_data):
    conn = setup_data
    loans.lend_equipment(conn, "EQ-1", 1, "100002", "2026-11-04", today="2026-11-04")
    with pytest.raises(RuleViolation) as info:
        loans.lend_equipment(conn, "EQ-1", 1, "100001", "2026-11-04", today="2026-11-04")
    assert info.value.message == "この備品は既に貸出中です"


def test_return_twice_is_rejected(setup_data):
    conn = setup_data
    with pytest.raises(RuleViolation) as info:
        loans.return_equipment(conn, "EQ-1", 1)
    assert info.value.message == "この備品は既に返却されています"


def test_borrower_is_required(setup_data):
    with pytest.raises(RuleViolation) as info:
        loans.lend_equipment(setup_data, "EQ-1", 1, "", "2026-11-04", today="2026-11-04")
    assert info.value.field == "borrower"


def test_future_date_is_rejected(setup_data):
    with pytest.raises(RuleViolation) as info:
        loans.lend_equipment(setup_data, "EQ-1", 1, "100002", "2026-11-05", today="2026-11-04")
    assert info.value.field == "lent_on"


def test_lend_with_stale_version_is_conflict(setup_data):
    with pytest.raises(RuleViolation) as info:
        loans.lend_equipment(setup_data, "EQ-1", 7, "100002", "2026-11-04", today="2026-11-04")
    assert info.value.level == "error"
