"""アカウントと備品の業務処理の単体テスト（SQLite の一時ファイルを使う）。"""

import sqlite3

import pytest

from equipment_ledger import accounts, db, equipment


@pytest.fixture
def conn(tmp_path):
    connection = db.connect_database(tmp_path)
    db.initialize_database(connection)
    yield connection
    connection.close()


def test_first_account_is_manager_then_employee(conn):
    role1, error1 = accounts.register_account(conn, "1234567", "山田", "password1")
    role2, error2 = accounts.register_account(conn, "2345678", "佐藤", "password2")
    assert (role1, error1) == ("manager", None)
    assert (role2, error2) == ("employee", None)


def test_duplicate_employee_number_is_rejected(conn):
    accounts.register_account(conn, "1234567", "山田", "password1")
    role, error = accounts.register_account(conn, "1234567", "別人", "password2")
    assert role is None
    assert error == "この社員番号は既に登録されています"
    count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    assert count == 1


def test_password_is_stored_hashed(conn):
    accounts.register_account(conn, "1234567", "山田", "password1")
    stored = conn.execute("SELECT password_hash FROM accounts").fetchone()[0]
    assert "password1" not in stored


def test_authenticate(conn):
    accounts.register_account(conn, "1234567", "山田", "password1")
    assert accounts.authenticate_account(conn, "1234567", "password1") is not None
    assert accounts.authenticate_account(conn, "1234567", "wrong-pass") is None
    assert accounts.authenticate_account(conn, "9999999", "password1") is None


def test_equipment_list_is_sorted_and_all_available(conn):
    for number, name in [("B-002", "b"), ("A-001", "a"), ("C-010", "c")]:
        assert equipment.create_equipment(conn, number, name) is None
    rows = equipment.list_equipment(conn)
    assert [row["equipment_number"] for row in rows] == ["A-001", "B-002", "C-010"]
    assert all(row["status"] == "空き" and row["borrower"] is None and row["lent_on"] is None for row in rows)


def test_equipment_number_uniqueness(conn):
    assert equipment.create_equipment(conn, "A-001", "a") is None
    assert equipment.create_equipment(conn, "A-001", "b") == "この管理番号は既に使われています"
    assert equipment.create_equipment(conn, "A-002", "c") is None
    revision = equipment.find_equipment(conn, "A-002")["revision"]
    assert equipment.update_equipment(conn, "A-002", revision, "A-001", "c") == "この管理番号は既に使われています"
    assert equipment.find_equipment(conn, "A-002") is not None


def test_update_and_delete(conn):
    equipment.create_equipment(conn, "A-001", "旧")
    revision = equipment.find_equipment(conn, "A-001")["revision"]
    assert equipment.update_equipment(conn, "A-001", revision, "A-100", "新") is None
    assert equipment.find_equipment(conn, "A-001") is None
    assert equipment.find_equipment(conn, "A-100")["name"] == "新"
    assert equipment.find_equipment(conn, "A-100")["revision"] == revision + 1
    assert equipment.delete_equipment(conn, "A-100") is None
    assert equipment.delete_equipment(conn, "A-100") == equipment.NOT_FOUND_MESSAGE
    assert equipment.list_equipment(conn) == []


def test_update_with_stale_revision_is_a_conflict(conn):
    equipment.create_equipment(conn, "A-001", "旧")
    stale = equipment.find_equipment(conn, "A-001")["revision"]
    assert equipment.update_equipment(conn, "A-001", stale, "A-001", "他人が直した") is None
    assert equipment.update_equipment(conn, "A-001", stale, "A-001", "古い画面") == equipment.CONFLICT_MESSAGE
    assert equipment.find_equipment(conn, "A-001")["name"] == "他人が直した"


def test_update_after_delete_is_a_conflict(conn):
    equipment.create_equipment(conn, "A-001", "旧")
    revision = equipment.find_equipment(conn, "A-001")["revision"]
    equipment.delete_equipment(conn, "A-001")
    assert equipment.update_equipment(conn, "A-001", revision, "A-001", "新") == equipment.CONFLICT_MESSAGE
    assert equipment.update_equipment(conn, "A-001", "not-a-number", "A-001", "新") == equipment.CONFLICT_MESSAGE


def test_initialize_adds_revision_to_a_stage1_database(tmp_path):
    """段 1 の DB（版番号の列が無い備品テーブル）を開き直すと、列が足され、既存の行が残る。"""
    old = db.connect_database(tmp_path)
    old.executescript(
        "CREATE TABLE equipment (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "equipment_number TEXT NOT NULL UNIQUE, name TEXT NOT NULL);"
        "INSERT INTO equipment (equipment_number, name) VALUES ('A-001', '旧い行');"
    )
    old.close()
    upgraded = db.connect_database(tmp_path)
    db.initialize_database(upgraded)
    row = equipment.find_equipment(upgraded, "A-001")
    assert row["name"] == "旧い行" and row["revision"] == 1
    upgraded.close()


def test_initialize_is_repeatable(conn):
    db.initialize_database(conn)
    db.initialize_database(conn)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO equipment (equipment_number, name) VALUES ('X', 'a')")
        conn.execute("INSERT INTO equipment (equipment_number, name) VALUES ('X', 'b')")
