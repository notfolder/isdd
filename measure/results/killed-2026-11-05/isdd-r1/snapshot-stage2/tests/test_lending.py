"""貸出・返却と版番号の業務処理の単体テスト（SQLite の一時ファイルを使う。同時の操作は 2 つの接続で再現する）。"""

import pytest

from equipment_ledger import accounts, db, equipment, lending


@pytest.fixture
def path(tmp_path):
    connection = db.connect_database(tmp_path)
    db.initialize_database(connection)
    accounts.register_account(connection, "1234567", "山田", "password1")  # 担当者
    accounts.register_account(connection, "2345678", "佐藤", "password2")  # 社員
    equipment.create_equipment(connection, "A-001", "ノート")
    equipment.create_equipment(connection, "A-002", "プロジェクター")
    connection.close()
    return tmp_path


def connect(path):
    connection = db.connect_database(path)
    db.initialize_database(connection)
    return connection


def borrower_id(conn, number):
    return conn.execute("SELECT id FROM accounts WHERE employee_number = ?", (number,)).fetchone()["id"]


def test_lend_then_list_shows_borrower_and_date(path):
    conn = connect(path)
    assert lending.lend_equipment(conn, "A-001", borrower_id(conn, "2345678"), "2026-11-05") is None
    row = {r["equipment_number"]: r for r in equipment.list_equipment(conn)}
    assert row["A-001"]["status"] == "貸出中"
    assert row["A-001"]["borrower"] == "佐藤"
    assert row["A-001"]["lent_on"] == "2026-11-05"
    assert row["A-002"]["status"] == "空き" and row["A-002"]["borrower"] is None
    conn.close()


def test_second_lend_of_a_lent_equipment_is_refused(path):
    first = connect(path)
    second = connect(path)  # 同時の別の担当者（別の接続）
    assert lending.lend_equipment(first, "A-001", borrower_id(first, "2345678"), "2026-11-05") is None
    assert lending.lend_equipment(second, "A-001", borrower_id(second, "1234567"), "2026-11-05") == (
        lending.ALREADY_LENT_MESSAGE
    )
    count = first.execute("SELECT COUNT(*) FROM loans").fetchone()[0]
    assert count == 1
    first.close()
    second.close()


def test_lend_with_missing_borrower_or_equipment(path):
    conn = connect(path)
    assert lending.lend_equipment(conn, "A-001", None, "2026-11-05") == lending.BORROWER_MISSING_MESSAGE
    assert lending.lend_equipment(conn, "A-001", 9999, "2026-11-05") == lending.BORROWER_MISSING_MESSAGE
    assert lending.lend_equipment(conn, "NOPE", borrower_id(conn, "2345678"), "2026-11-05") == (
        equipment.NOT_FOUND_MESSAGE
    )
    conn.close()


def test_return_clears_the_record_and_second_return_is_refused(path):
    first = connect(path)
    second = connect(path)
    lending.lend_equipment(first, "A-001", borrower_id(first, "2345678"), "2026-11-05")
    assert lending.return_equipment(first, "A-001") is None
    assert lending.return_equipment(second, "A-001") == lending.ALREADY_RETURNED_MESSAGE
    assert first.execute("SELECT COUNT(*) FROM loans").fetchone()[0] == 0
    assert lending.return_equipment(first, "NOPE") == equipment.NOT_FOUND_MESSAGE
    first.close()
    second.close()


def test_lent_equipment_cannot_be_deleted_until_returned(path):
    conn = connect(path)
    lending.lend_equipment(conn, "A-001", borrower_id(conn, "2345678"), "2026-11-05")
    assert equipment.delete_equipment(conn, "A-001") == equipment.LENT_DELETE_MESSAGE
    assert equipment.find_equipment(conn, "A-001") is not None
    lending.return_equipment(conn, "A-001")
    assert equipment.delete_equipment(conn, "A-001") is None
    conn.close()


def test_update_keeps_the_lending_record(path):
    conn = connect(path)
    lending.lend_equipment(conn, "A-001", borrower_id(conn, "2345678"), "2026-11-05")
    revision = equipment.find_equipment(conn, "A-001")["revision"]
    assert equipment.update_equipment(conn, "A-001", revision, "A-900", "改名したノート") is None
    row = {r["equipment_number"]: r for r in equipment.list_equipment(conn)}
    assert row["A-900"]["status"] == "貸出中"
    assert row["A-900"]["borrower"] == "佐藤"
    assert row["A-900"]["lent_on"] == "2026-11-05"
    conn.close()


def test_is_lent(path):
    conn = connect(path)
    assert lending.is_lent(conn, "A-001") is False
    lending.lend_equipment(conn, "A-001", borrower_id(conn, "2345678"), "2026-11-05")
    assert lending.is_lent(conn, "A-001") is True
    assert lending.is_lent(conn, "NOPE") is False
    conn.close()
