"""アカウントの検査・登録・認証の単体・結合テスト。"""

from app import accounts
from app.db import get_db


def test_validate_registration_accepts_valid_values():
    assert accounts.validate_registration("000123", "山田太郎", "password1") == {}


def test_validate_registration_reports_each_field():
    errors = accounts.validate_registration("12345", "", "1234567")
    assert errors == {
        "employee_number": "社員番号は 6 桁の数字で入力してください",
        "name": "名前を入力してください",
        "password": "パスワードは 8 文字以上で入力してください",
    }


def test_validate_registration_rejects_long_name_and_non_ascii_digits():
    assert accounts.validate_registration("123456", "あ" * 31, "password1")["name"] == (
        "名前は 30 文字以内で入力してください"
    )
    assert "employee_number" in accounts.validate_registration("１２３４５６", "名前", "password1")


def test_first_account_is_manager_and_second_is_employee(app):
    with app.app_context():
        first_id, errors = accounts.register_account("000001", "一人目", "password1")
        second_id, _ = accounts.register_account("000002", "二人目", "password2")
        assert errors == {}
        assert accounts.get_account(first_id)["role"] == "manager"
        assert accounts.get_account(second_id)["role"] == "employee"


def test_duplicate_employee_number_is_rejected(app):
    with app.app_context():
        accounts.register_account("000001", "一人目", "password1")
        account_id, errors = accounts.register_account("000001", "別人", "password2")
        assert account_id is None
        assert errors == {"employee_number": "この社員番号は既に登録されています"}


def test_password_is_stored_as_hash(app):
    with app.app_context():
        accounts.register_account("000001", "一人目", "password1")
        row = get_db().execute("SELECT password_hash FROM accounts").fetchone()
        assert row["password_hash"] != "password1"


def test_authenticate_account_success_and_failure(app):
    with app.app_context():
        accounts.register_account("000001", "一人目", "password1")
        assert accounts.authenticate_account("000001", "password1")["name"] == "一人目"
        assert accounts.authenticate_account("000001", "wrong-pass") is None
        assert accounts.authenticate_account("999999", "password1") is None
