"""アカウント登録とログインの E2E テスト（RQ-TS-REGISTER-FIRST-ACCOUNT、RQ-TS-REGISTER-SECOND-ACCOUNT、RQ-TS-LOGIN-LOGOUT）。"""
from playwright.sync_api import expect


def test_register_first_account(page, ui, expect_):
    ui.register("000001", "総務 太郎", "password123")
    expect(page.locator(".message")).to_have_text("登録しました。ログインしてください")
    ui.login("000001", "password123")
    expect(page.locator(".current-user")).to_have_text("総務 太郎")
    expect(page.get_by_role("link", name="備品を登録")).to_be_visible()


def test_register_second_account(page, ui, expect_):
    ui.register("000001", "総務 太郎", "password123")
    page.wait_for_url("**/login/")
    ui.register("00002", "社員 花子", "password123")
    expect(page.locator("#id_employee_number").locator("..").locator(".field-error")).to_be_visible()
    expect(page.locator("#id_employee_number")).to_have_value("00002")
    ui.register("000002", "あ" * 31, "password123")
    expect(page.locator("#id_name").locator("..").locator(".field-error")).to_be_visible()
    expect(page.locator("#id_name")).to_have_value("あ" * 31)
    ui.register("000002", "社員 花子", "1234567")
    expect(page.locator("#id_password").locator("..").locator(".field-error")).to_be_visible()
    ui.register("000001", "社員 花子", "password123")
    expect(page.locator("#id_employee_number").locator("..").locator(".field-error")).to_be_visible()
    ui.register("000002", "社員 花子", "password123")
    expect(page.locator(".message")).to_have_text("登録しました。ログインしてください")
    ui.login("000002", "password123")
    expect(page.locator(".current-user")).to_have_text("社員 花子")
    expect(page.get_by_role("link", name="備品を登録")).to_have_count(0)


def test_login_logout(page, ui, expect_):
    ui.register("000001", "総務 太郎", "password123")
    page.wait_for_url("**/login/")
    ui.login("000001", "wrong-pass")
    expect(page.locator(".error")).to_have_text("社員番号またはパスワードが違います")
    ui.login("000001", "password123")
    expect(page.locator(".current-user")).to_have_text("総務 太郎")
    ui.logout()
    expect(page.locator(".current-user")).to_have_count(0)
    expect(page.get_by_role("link", name="ログイン")).to_be_visible()
