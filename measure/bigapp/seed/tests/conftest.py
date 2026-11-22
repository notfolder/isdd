"""テストの共通の部品。"""

import pytest

from app import create_app
from app.core.db import ADMIN_NO, ADMIN_PASSWORD


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_TODAY", "2026-06-15")
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite3")})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin(client):
    """総務の担当者（最初から居る管理用の社員）でログインしたクライアント"""
    client.post("/login", data={"employee_no": ADMIN_NO, "password": ADMIN_PASSWORD})
    return client


@pytest.fixture
def make_employee(admin):
    """社員を登録する。make_employee("100001", "山田", role="employee")"""

    def make(number, name="社員", role="employee", dept="営業部"):
        response = admin.post("/employees/new", data={"employee_no": number, "name": name, "role": role, "dept": dept})
        assert response.status_code == 201, response.get_data(as_text=True)
        return number

    return make


@pytest.fixture
def set_today(monkeypatch):
    """今日の日付を替える。set_today("2026-07-01")"""

    def setter(text):
        monkeypatch.setenv("APP_TODAY", text)

    return setter
