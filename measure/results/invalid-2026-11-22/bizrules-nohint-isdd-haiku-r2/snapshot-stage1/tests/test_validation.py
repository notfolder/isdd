"""入力の検査の境界値を確かめる。"""

from datetime import date

import pytest

from service.validation import validate_account_fields, validate_equipment_fields, validate_lending_fields


@pytest.mark.parametrize("number, ok", [("100001", True), ("12345", False), ("1234567", False),
                                        ("12345a", False), ("", False)])
def test_employee_number_must_be_six_digits(number, ok):
    errors = validate_account_fields(number, "山田", "password1")
    assert ("employee_number" not in errors) is ok


def test_name_length_limits_after_trim():
    assert "name" in validate_account_fields("100001", "   ", "password1")
    assert "name" not in validate_account_fields("100001", "a" * 30, "password1")
    assert "name" in validate_account_fields("100001", "a" * 31, "password1")
    assert "name" not in validate_account_fields("100001", "  山田  ", "password1")


def test_password_minimum_eight_characters():
    assert "password" in validate_account_fields("100001", "山田", "1234567")
    assert "password" not in validate_account_fields("100001", "山田", "12345678")


def test_valid_account_has_no_errors():
    assert validate_account_fields("100001", "山田 太郎", "password1") == {}


@pytest.mark.parametrize("number, ok", [("EQ-0001", True), ("A" * 20, True), ("A" * 21, False),
                                        ("EQ 0002", False), ("EQ_1", False), ("", False),
                                        ("日本-1", False)])
def test_equipment_number_format(number, ok):
    errors = validate_equipment_fields(number, "ノート PC")
    assert ("equipment_number" not in errors) is ok


def test_equipment_name_length():
    assert "name" in validate_equipment_fields("EQ-1", "")
    assert "name" not in validate_equipment_fields("EQ-1", "a" * 50)
    assert "name" in validate_equipment_fields("EQ-1", "a" * 51)


def test_lending_borrower_required():
    errors, borrower_id, _ = validate_lending_fields("", "2026-11-20", date(2026, 11, 22))
    assert "borrower" in errors and borrower_id is None
    errors, borrower_id, _ = validate_lending_fields("7", "2026-11-20", date(2026, 11, 22))
    assert errors == {} and borrower_id == 7


def test_lending_date_rules():
    today = date(2026, 11, 22)
    assert validate_lending_fields("1", "", today)[0]["lent_on"]
    assert validate_lending_fields("1", "2026/11/22", today)[0]["lent_on"]
    assert validate_lending_fields("1", "2026-02-30", today)[0]["lent_on"]
    assert validate_lending_fields("1", "2026-11-23", today)[0]["lent_on"] == "貸出日は今日以前の日付を入力してください"
    assert validate_lending_fields("1", "2026-11-22", today)[0] == {}
    assert validate_lending_fields("1", "2026-01-01", today)[0] == {}
