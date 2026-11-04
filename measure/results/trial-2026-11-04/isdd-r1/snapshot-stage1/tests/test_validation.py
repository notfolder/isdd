"""入力の検証の文言と規則を確かめる。"""

import pytest

from app import validation


@pytest.mark.parametrize(
    "number, expected",
    [("12345", "社員番号は 6 桁の数字で入力してください"), ("1234567", "社員番号は 6 桁の数字で入力してください"), ("12345a", "社員番号は 6 桁の数字で入力してください"), ("100001", None)],
)
def test_employee_number(number, expected):
    errors = validation.validate_account_input(number, "名前", "password1")
    assert errors.get("employee_number") == expected


def test_name_limits():
    assert validation.validate_account_input("100001", "", "password1")["name"] == "名前を入力してください"
    assert validation.validate_account_input("100001", "a" * 31, "password1")["name"] == "名前は 30 文字以内で入力してください"
    assert "name" not in validation.validate_account_input("100001", "a" * 30, "password1")


def test_password_minimum():
    assert validation.validate_password("1234567") == "パスワードは 8 文字以上で入力してください"
    assert validation.validate_password("12345678") is None


@pytest.mark.parametrize("number, ok", [("EQ-0001", True), ("A" * 20, True), ("A" * 21, False), ("備品1", False), ("", False)])
def test_equipment_number(number, ok):
    errors = validation.validate_equipment_input(number, "名前")
    assert ("equipment_number" not in errors) is ok


def test_equipment_name_limit():
    assert validation.validate_equipment_input("EQ-1", "a" * 51)["name"] == "備品名は 50 文字以内で入力してください"
    assert "name" not in validation.validate_equipment_input("EQ-1", "a" * 50)


def test_lent_on_rules():
    assert validation.validate_lent_on("2026-11-05", "2026-11-04") == "貸出日に未来の日付は入力できません"
    assert validation.validate_lent_on("2026-11-04", "2026-11-04") is None
    assert validation.validate_lent_on("2026/11/04", "2026-11-04") == "貸出日は日付で入力してください"
