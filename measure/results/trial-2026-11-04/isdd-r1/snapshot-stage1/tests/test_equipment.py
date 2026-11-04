"""備品の業務処理を確かめる（登録、重複、版番号による同時更新の検出、貸出中の削除）。"""

import pytest

from app import equipment, loans, accounts
from app.errors import RuleViolation


def test_create_and_list_status(conn):
    equipment.create_equipment(conn, "EQ-0002", "椅子")
    equipment.create_equipment(conn, "EQ-0001", "ノートPC")
    rows = equipment.list_lending_status(conn)
    assert [row["equipment_number"] for row in rows] == ["EQ-0001", "EQ-0002"]
    assert all(row["lent_on"] is None for row in rows)


def test_duplicate_number_is_rejected(conn):
    equipment.create_equipment(conn, "EQ-1", "椅子")
    with pytest.raises(RuleViolation) as info:
        equipment.create_equipment(conn, "EQ-1", "別の椅子")
    assert info.value.field == "equipment_number"


def test_update_with_stale_version_is_conflict(conn):
    equipment.create_equipment(conn, "EQ-1", "椅子")
    equipment.update_equipment(conn, "EQ-1", "EQ-1", "椅子A", expected_version=1)
    with pytest.raises(RuleViolation) as info:
        equipment.update_equipment(conn, "EQ-1", "EQ-1", "椅子B", expected_version=1)
    assert info.value.level == "error"
    assert info.value.message.startswith("他の担当者が先にこの備品を更新しました")


def test_rename_moves_active_loan(conn):
    accounts.register_account(conn, "100001", "山田", "password1")
    equipment.create_equipment(conn, "EQ-1", "椅子")
    loans.lend_equipment(conn, "EQ-1", 1, "100001", "2026-11-04", today="2026-11-04")
    equipment.update_equipment(conn, "EQ-1", "EQ-9", "椅子", expected_version=1)
    rows = equipment.list_lending_status(conn)
    assert rows[0]["equipment_number"] == "EQ-9" and rows[0]["borrower_name"] == "山田"


def test_cannot_delete_lent_equipment(conn):
    accounts.register_account(conn, "100001", "山田", "password1")
    equipment.create_equipment(conn, "EQ-1", "椅子")
    loans.lend_equipment(conn, "EQ-1", 1, "100001", "2026-11-04", today="2026-11-04")
    with pytest.raises(RuleViolation) as info:
        equipment.delete_equipment(conn, "EQ-1", 1)
    assert info.value.message == "この備品は貸出中のため削除できません。先に返却を処理してください"


def test_delete_with_stale_version_is_conflict(conn):
    equipment.create_equipment(conn, "EQ-1", "椅子")
    with pytest.raises(RuleViolation) as info:
        equipment.delete_equipment(conn, "EQ-1", 99)
    assert info.value.level == "error"
    equipment.delete_equipment(conn, "EQ-1", 1)
    assert equipment.get_equipment(conn, "EQ-1") is None
