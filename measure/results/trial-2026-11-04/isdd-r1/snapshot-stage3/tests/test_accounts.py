"""アカウントの業務処理を確かめる（担当者の初期化、認証、担当者 1 人以上、削除の制限）。"""

import pytest

from app import accounts, loans, equipment
from app.errors import RuleViolation


def test_first_account_is_manager_and_second_is_employee(conn):
    assert accounts.register_account(conn, "100001", "山田", "password1") is True
    assert accounts.register_account(conn, "100002", "佐藤", "password2") is False


def test_duplicate_employee_number_is_rejected(conn):
    accounts.register_account(conn, "100001", "山田", "password1")
    with pytest.raises(RuleViolation) as info:
        accounts.register_account(conn, "100001", "別人", "password1")
    assert info.value.field == "employee_number"
    assert info.value.message == "この社員番号は既に登録されています"


def test_authenticate(conn):
    accounts.register_account(conn, "100001", "山田", "password1")
    assert accounts.authenticate(conn, "100001", "password1") == "100001"
    assert accounts.authenticate(conn, "100001", "wrong-pass") is None
    assert accounts.authenticate(conn, "999999", "password1") is None


def test_password_is_stored_as_hash(conn):
    accounts.register_account(conn, "100001", "山田", "password1")
    stored = conn.execute("SELECT password_hash FROM accounts").fetchone()[0]
    assert stored != "password1" and "password1" not in stored


def test_cannot_remove_last_manager(conn):
    accounts.register_account(conn, "100001", "山田", "password1")
    with pytest.raises(RuleViolation) as info:
        accounts.set_manager_role(conn, "100001", grant=False)
    assert info.value.message == "担当者が 1 人もいなくなるため、この操作はできません"


def test_manager_can_be_revoked_when_another_exists(conn):
    accounts.register_account(conn, "100001", "山田", "password1")
    accounts.register_account(conn, "100002", "佐藤", "password2")
    accounts.set_manager_role(conn, "100002", grant=True)
    accounts.set_manager_role(conn, "100001", grant=False)
    assert [row["is_manager"] for row in accounts.list_accounts(conn)] == [0, 1]


def test_cannot_delete_borrowing_account(conn):
    accounts.register_account(conn, "100001", "山田", "password1")
    accounts.register_account(conn, "100002", "佐藤", "password2")
    equipment.create_equipment(conn, "EQ-1", "椅子")
    loans.lend_equipment(conn, "EQ-1", 1, "100002", "2026-11-04", today="2026-11-04")
    with pytest.raises(RuleViolation) as info:
        accounts.delete_account(conn, "100002")
    assert info.value.message == "この社員は備品を借りているため削除できません。先に返却を処理してください"


def test_delete_account_removes_its_sessions(conn):
    accounts.register_account(conn, "100001", "山田", "password1")
    accounts.register_account(conn, "100002", "佐藤", "password2")
    conn.execute("INSERT INTO sessions (token, employee_number, last_seen) VALUES ('t', '100002', 0)")
    accounts.delete_account(conn, "100002")
    assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0


def test_reset_password_changes_login(conn):
    accounts.register_account(conn, "100001", "山田", "password1")
    accounts.reset_password(conn, "100001", "newpassword")
    assert accounts.authenticate(conn, "100001", "newpassword") == "100001"
    assert accounts.authenticate(conn, "100001", "password1") is None
