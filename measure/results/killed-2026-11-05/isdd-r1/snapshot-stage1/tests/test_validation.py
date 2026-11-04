"""入力の検証の単体テスト。"""

from equipment_ledger.validation import validate_account_input, validate_equipment_input


def test_account_valid():
    values, errors = validate_account_input(" 123456 ", " 山田太郎 ", "password1")
    assert errors == {}
    assert values["employee_number"] == "123456"
    assert values["name"] == "山田太郎"


def test_account_employee_number_must_be_six_digits():
    for number in ["12345", "1234567", "12345a", "", "１２３４５６"]:
        _, errors = validate_account_input(number, "名前", "password1")
        assert errors["employee_number"] == "社員番号は 6 桁の数字で入力してください"


def test_account_name_bounds():
    _, errors = validate_account_input("123456", "   ", "password1")
    assert errors["name"] == "名前を入力してください"
    _, errors = validate_account_input("123456", "a" * 30, "password1")
    assert "name" not in errors
    _, errors = validate_account_input("123456", "a" * 31, "password1")
    assert errors["name"] == "名前は 30 文字以内で入力してください"


def test_account_password_minimum():
    _, errors = validate_account_input("123456", "名前", "1234567")
    assert errors["password"] == "パスワードは 8 文字以上で入力してください"
    _, errors = validate_account_input("123456", "名前", "12345678")
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
