"""段 1: アカウントの登録・ログイン・自動ログアウト・社員の制限。"""

import re
import time

import pytest
from playwright.sync_api import expect

from support.ui import field_error, login, messages, register

STAFF = {"number": "000001", "name": "担当太郎", "staff": True}
EMPLOYEE = {"number": "000002", "name": "社員花子"}
STAFF_ONLY = "この操作は担当者だけが行えます"


@pytest.mark.stage1
def test_first_account_becomes_staff(app, page):
    page.goto(app.base_url)
    page.get_by_role("link", name="アカウント登録").click()
    register(page, app.base_url, "000001", "最初の人")
    login(page, app.base_url, "000001")
    expect(page.get_by_role("button", name="備品を登録")).to_be_visible()
    page.get_by_role("button", name="ログアウト").click()
    register(page, app.base_url, "000002", "二番目の人")
    login(page, app.base_url, "000002")
    expect(page.get_by_role("button", name="ログアウト")).to_be_visible()
    expect(page.get_by_role("button", name="備品を登録")).to_have_count(0)


@pytest.mark.stage1
def test_account_registration(app, page):
    app.seed({"accounts": [STAFF]})
    cases = [
        ({"number": "12345"}, "id_employee_number", "社員番号は 6 桁の数字で入力してください"),
        ({"number": "A12345"}, "id_employee_number", "社員番号は 6 桁の数字で入力してください"),
        ({"number": "000001"}, "id_employee_number", "この社員番号は既に登録されています"),
        ({"name": "あ" * 31}, "id_name", "名前は 30 文字以内で入力してください"),
        ({"password": "a" * 7}, "id_password", "パスワードは 8 文字以上で入力してください"),
        ({"name": ""}, "id_name", "名前を入力してください"),
    ]
    for override, input_id, message in cases:
        values = {"number": "000005", "name": "新人", "password": "password1", **override}
        register(page, app.base_url, values["number"], values["name"], values["password"])
        expect(field_error(page, input_id)).to_have_text(message)
        expect(page.locator("#id_employee_number")).to_have_value(values["number"])
        expect(page.locator("#id_name")).to_have_value(values["name"])
    register(page, app.base_url, "000005", "新人")
    expect(page).to_have_url(f"{app.base_url}/login/")
    expect(page.get_by_text("登録しました。ログインしてください")).to_be_visible()


@pytest.mark.stage1
def test_login_logout(app, page):
    app.seed({"accounts": [STAFF, EMPLOYEE]})
    for number, password in [("000002", "wrongpass"), ("999999", "password1")]:
        login(page, app.base_url, number, password)
        expect(page.locator(".error")).to_have_text(["社員番号またはパスワードが違います"])
    login(page, app.base_url, "000002")
    expect(page).to_have_url(f"{app.base_url}/")
    expect(page.locator(".current-user")).to_have_text("社員花子")
    page.get_by_role("button", name="ログアウト").click()
    expect(page.get_by_role("link", name="ログイン")).to_be_visible()
    expect(page.get_by_role("button", name="ログアウト")).to_have_count(0)


@pytest.mark.stage1
def test_session_timeout(app_with_short_session, page):
    app = app_with_short_session
    app.seed({"accounts": [STAFF]})
    login(page, app.base_url, "000001")
    time.sleep(4)
    page.get_by_role("button", name="備品を登録").click()
    expect(page).to_have_url(re.compile(re.escape(f"{app.base_url}/equipment/new/") + r"\??$"))
    page.goto(app.base_url)
    time.sleep(7)
    page.get_by_role("button", name="備品を登録").click()
    expect(page).to_have_url(f"{app.base_url}/login/")


@pytest.mark.stage1
def test_employee_cannot_manage_equipment(app, page):
    app.seed({"accounts": [STAFF, EMPLOYEE], "equipment": [{"number": "PC-001", "name": "ノートパソコン"}]})
    login(page, app.base_url, "000002")
    expect(page.get_by_role("button", name="備品を登録")).to_have_count(0)
    expect(page.get_by_role("button", name="修正")).to_have_count(0)
    expect(page.get_by_role("button", name="削除")).to_have_count(0)
    page.goto(f"{app.base_url}/equipment/new/")
    expect(page).to_have_url(f"{app.base_url}/")
    expect(messages(page)).to_have_text([STAFF_ONLY])
    page.get_by_role("button", name="ログアウト").click()
    page.goto(f"{app.base_url}/equipment/new/")
    expect(page).to_have_url(f"{app.base_url}/login/")
