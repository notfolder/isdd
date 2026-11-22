"""貸出状況の閲覧と権限の E2E テスト（RQ-TS-VIEW-STATUS-PUBLIC、RQ-TS-EMPLOYEE-CANNOT-OPERATE）。"""
from playwright.sync_api import expect


def test_view_status_public(page, ui, expect_):
    page.goto("/")
    expect(page.locator("body")).to_contain_text("備品は登録されていません")
    ui.register("000001", "総務 太郎", "password123")
    page.wait_for_url("**/login/")
    ui.login("000001", "password123")
    page.wait_for_url("**/")
    ui.register_equipment("ZZ-0009", "プロジェクター")
    ui.register_equipment("AA-0001", "ノート PC")
    ui.logout()
    page.goto("/")
    rows = page.locator("tbody tr")
    expect(rows).to_have_count(2)
    expect(rows.nth(0)).to_have_attribute("data-equipment-number", "AA-0001")
    expect(rows.nth(1)).to_have_attribute("data-equipment-number", "ZZ-0009")
    expect(rows.nth(0)).to_contain_text("ノート PC")
    expect(page.get_by_role("button", name="修正")).to_have_count(0)
    expect(page.get_by_role("button", name="貸出")).to_have_count(0)


def test_employee_cannot_operate(page, ui, expect_):
    ui.register("000001", "総務 太郎", "password123")
    page.wait_for_url("**/login/")
    ui.login("000001", "password123")
    page.wait_for_url("**/")
    ui.register_equipment("AB-0001", "ノート PC")
    ui.logout()
    ui.register("000002", "社員 花子", "password123")
    page.wait_for_url("**/login/")
    ui.login("000002", "password123")
    page.wait_for_url("**/")
    expect(page.get_by_role("button", name="修正")).to_have_count(0)
    expect(page.get_by_role("button", name="削除")).to_have_count(0)
    page.goto("/equipment/new/")
    expect(page.locator(".error")).to_have_text("この操作は担当者だけができます")
    page.goto("/")
    expect(page.locator('tr[data-equipment-number="AB-0001"]')).to_have_count(1)
