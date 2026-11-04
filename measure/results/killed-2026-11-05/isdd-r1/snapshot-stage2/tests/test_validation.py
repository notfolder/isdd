"""入力の検証の単体テスト。"""

from datetime import date

from equipment_ledger.validation import (
    validate_account_input,
    validate_equipment_input,
    validate_lending_input,
)


def test_account_valid():
    values, errors = validate_account_input(" 1234567 ", " 山田太郎 ", "password1")
    assert errors == {}
    assert values["employee_number"] == "1234567"
    assert values["name"] == "山田太郎"


def test_account_employee_number_must_be_six_digits():
    for number in ["123456", "12345678", "12345a", "", "１２３４５６７"]:
        _, errors = validate_account_input(number, "名前", "password1")
        assert errors["employee_number"] == "社員番号は 7 桁の数字で入力してください"


def test_account_name_bounds():
    _, errors = validate_account_input("1234567", "   ", "password1")
    assert errors["name"] == "名前を入力してください"
    _, errors = validate_account_input("1234567", "a" * 30, "password1")
    assert "name" not in errors
    _, errors = validate_account_input("1234567", "a" * 31, "password1")
    assert errors["name"] == "名前は 30 文字以内で入力してください"


def test_account_password_minimum():
    _, errors = validate_account_input("1234567", "名前", "1234567")
    assert errors["password"] == "パスワードは 8 文字以上で入力してください"
    _, errors = validate_account_input("1234567", "名前", "12345678")
    assert "password" not in errors


def test_equipment_number_rules():
    _, errors = validate_equipment_input("PC-0001", "ノート")
    assert errors == {}
    for number in ["a" * 21, "PC 001", "備品1", ""]:
        _, errors = validate_equipment_input(number, "ノート")
        assert errors["equipment_number"] == "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください"
    _, errors = validate_equipment_input("a" * 20, "ノート")
    assert "equipment_number" not in errors


def test_equipment_name_rules():
    _, errors = validate_equipment_input("A-1", "")
    assert errors["name"] == "備品名を入力してください"
    _, errors = validate_equipment_input("A-1", "a" * 51)
    assert errors["name"] == "備品名は 50 文字以内で入力してください"
    _, errors = validate_equipment_input("A-1", "a" * 50)
    assert "name" not in errors


TODAY = date(2026, 11, 5)


def test_lending_valid_today_and_past():
    values, errors = validate_lending_input("3", "2026-11-05", TODAY)
    assert errors == {} and values == {"borrower_id": 3, "lent_on": "2026-11-05"}
    _, errors = validate_lending_input("3", "2026-01-01", TODAY)
    assert errors == {}


def test_lending_future_date_is_refused():
    _, errors = validate_lending_input("3", "2026-11-06", TODAY)
    assert errors["lent_on"] == "貸出日に未来の日付は入力できません"


def test_lending_date_format_and_empty():
    for text in ["2026/11/05", "2026-13-01", "2026-02-30", "20261105"]:
        _, errors = validate_lending_input("3", text, TODAY)
        assert errors["lent_on"] == "貸出日は YYYY-MM-DD の形式で入力してください"
    _, errors = validate_lending_input("3", "   ", TODAY)
    assert errors["lent_on"] == "貸出日を入力してください"


def test_lending_borrower_must_be_chosen():
    for text in ["", "  ", None]:
        values, errors = validate_lending_input(text, "2026-11-05", TODAY)
        assert values["borrower_id"] is None
        assert errors["borrower_id"] == "借りる社員を選んでください"
