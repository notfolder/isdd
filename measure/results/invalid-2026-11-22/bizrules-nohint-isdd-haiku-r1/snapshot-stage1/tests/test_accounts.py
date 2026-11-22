"""アカウント登録とログインの単体・結合テスト。"""
import pytest
from django.urls import reverse

from accounts.forms import RegisterForm
from accounts.models import Account, Role
from accounts.services import register_account


def test_first_registered_account_becomes_manager(db):
    account = register_account("000001", "総務 太郎", "password123")
    assert account.role == Role.MANAGER


def test_later_registered_account_becomes_employee(db, make_account):
    make_account("000001", role=Role.MANAGER)
    account = register_account("000002", "社員 花子", "password123")
    assert account.role == Role.EMPLOYEE


@pytest.mark.parametrize("number", ["12345", "1234567", "12345a", "ABCDEF"])
def test_employee_number_must_be_six_digits(db, number):
    form = RegisterForm({"employee_number": number, "name": "名前", "password": "password123"})
    assert not form.is_valid()
    assert "employee_number" in form.errors


def test_employee_number_duplicate_is_rejected(db, make_account):
    make_account("000001")
    form = RegisterForm({"employee_number": "000001", "name": "名前", "password": "password123"})
    assert not form.is_valid()
    assert "既に登録" in form.errors["employee_number"][0]


def test_name_over_30_characters_is_rejected(db):
    form = RegisterForm({"employee_number": "000001", "name": "あ" * 31, "password": "password123"})
    assert not form.is_valid()
    assert "name" in form.errors


def test_password_under_8_characters_is_rejected(db):
    form = RegisterForm({"employee_number": "000001", "name": "名前", "password": "1234567"})
    assert not form.is_valid()
    assert "password" in form.errors


def test_password_keeps_surrounding_spaces(db):
    form = RegisterForm({"employee_number": "000001", "name": "名前", "password": " password1 "})
    assert form.is_valid()
    assert form.cleaned_data["password"] == " password1 "


def test_password_is_stored_hashed(db):
    account = register_account("000001", "名前", "password123")
    stored = Account.objects.get(pk=account.pk).password
    assert stored != "password123"
    assert account.check_password("password123")


def test_login_succeeds_with_correct_password(client, make_account):
    make_account("000001", password="password123")
    response = client.post(reverse("login"), {"employee_number": "000001", "password": "password123"})
    assert response.status_code == 302
    assert response.url == reverse("status")


def test_login_failure_shows_error(client, make_account):
    make_account("000001", password="password123")
    response = client.post(reverse("login"), {"employee_number": "000001", "password": "wrong-pass"})
    assert response.status_code == 200
    assert "社員番号またはパスワードが違います" in response.content.decode()


def test_allowed_hosts_default_is_local_only(monkeypatch):
    monkeypatch.delenv("ALLOWED_HOSTS", raising=False)
    import importlib

    import config.settings as current

    reloaded = importlib.reload(current)
    assert reloaded.ALLOWED_HOSTS == ["localhost", "127.0.0.1"]
