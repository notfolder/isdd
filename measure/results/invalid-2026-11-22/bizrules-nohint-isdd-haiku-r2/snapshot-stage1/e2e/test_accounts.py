"""アカウント登録とログインの E2E。"""

from playwright.sync_api import expect

from helpers import create_equipment, login, logout, register


def test_first_account_is_manager(server, page):
    register(page, server, "100001", "山田 太郎")
    expect(page).to_have_url(server.url("/login/"))
    login(page, server, "100001")
    expect(page.locator(".current-user")).to_have_text("山田 太郎")
    expect(page.get_by_role("link", name="備品を登録")).to_be_visible()


def test_second_account_is_member(server, page):
    register(page, server, "100001", "山田 太郎")
    login(page, server, "100001")
    create_equipment(page, server, "EQ-0001", "ノート PC 14 インチ")
    logout(page)
    register(page, server, "100002", "佐藤 花子")
    login(page, server, "100002")
    expect(page.locator(".current-user")).to_have_text("佐藤 花子")
    expect(page.get_by_role("link", name="備品を登録")).to_have_count(0)
    expect(page.locator("tbody button")).to_have_count(0)


def test_reject_invalid_account(server, page):
    register(page, server, "100001", "山田 太郎")
    page.goto(server.url("/accounts/register/"))
    page.locator("#id_employee_number").fill("12345")
    page.locator("#id_name").fill("")
    page.locator("#id_password").fill("1234567")
    page.get_by_role("button", name="登録", exact=True).click()
    expect(page.locator(".field:has(#id_employee_number) .field-error")).to_be_visible()
    expect(page.locator(".field:has(#id_name) .field-error")).to_be_visible()
    expect(page.locator(".field:has(#id_password) .field-error")).to_be_visible()
    expect(page.locator("#id_employee_number")).to_have_value("12345")
    expect(page.locator("#id_password")).to_have_value("1234567")

    page.locator("#id_employee_number").fill("100001")
    page.locator("#id_name").fill("別の人")
    page.locator("#id_password").fill("password1")
    page.get_by_role("button", name="登録", exact=True).click()
    expect(page.locator(".field:has(#id_employee_number) .field-error")).to_have_text(
        "この社員番号は登録されています")
    expect(page.locator("#id_employee_number")).to_have_value("100001")


def test_login_logout(server, page):
    register(page, server, "100001", "山田 太郎")
    login(page, server, "100001")
    expect(page.locator(".current-user")).to_have_text("山田 太郎")
    logout(page)
    expect(page.locator(".current-user")).to_have_count(0)
    expect(page.get_by_role("link", name="ログイン")).to_be_visible()
    expect(page.get_by_role("link", name="アカウント登録")).to_be_visible()


def test_login_failure(server, page):
    register(page, server, "100001", "山田 太郎")
    login(page, server, "100001", password="wrong-password")
    expect(page.locator(".error")).to_have_text("社員番号またはパスワードが違います")
    expect(page.locator(".current-user")).to_have_count(0)
