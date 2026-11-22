"""備品の登録・修正・削除の E2E テスト（RQ-TS-REGISTER-EQUIPMENT、RQ-TS-UPDATE-EQUIPMENT、RQ-TS-DELETE-EQUIPMENT）。"""
from playwright.sync_api import expect


def _manager(ui, page):
    ui.register("000001", "総務 太郎", "password123")
    page.wait_for_url("**/login/")
    ui.login("000001", "password123")
    page.wait_for_url("**/")


def test_register_equipment(page, ui, expect_):
    _manager(ui, page)
    ui.register_equipment("AB-0001", "ノート PC")
    expect(page.locator('tr[data-equipment-number="AB-0001"]')).to_contain_text("ノート PC")
    ui.register_equipment("AB-0001", "重複")
    expect(page.locator("#id_equipment_number").locator("..").locator(".field-error")).to_be_visible()
    expect(page.locator("#id_equipment_number")).to_have_value("AB-0001")
    page.fill("#id_equipment_number", "全角１")
    page.fill("#id_name", "備品")
    page.get_by_role("button", name="保存").click()
    expect(page.locator("#id_equipment_number").locator("..").locator(".field-error")).to_be_visible()


def test_update_equipment(page, ui, expect_):
    _manager(ui, page)
    ui.register_equipment("AB-0001", "ノート PC")
    ui.register_equipment("AB-0002", "プロジェクター")
    page.locator('tr[data-equipment-number="AB-0001"]').get_by_role("button", name="修正").click()
    page.fill("#id_name", "ノート PC（更新）")
    page.get_by_role("button", name="保存").click()
    expect(page.locator('tr[data-equipment-number="AB-0001"]')).to_contain_text("ノート PC（更新）")
    page.locator('tr[data-equipment-number="AB-0001"]').get_by_role("button", name="修正").click()
    page.fill("#id_equipment_number", "AB-0002")
    page.get_by_role("button", name="保存").click()
    expect(page.locator("#id_equipment_number").locator("..").locator(".field-error")).to_be_visible()
    page.goto("/")
    expect(page.locator('tr[data-equipment-number="AB-0001"]')).to_contain_text("ノート PC（更新）")
    expect(page.locator('tr[data-equipment-number="AB-0002"]')).to_contain_text("プロジェクター")


def test_delete_equipment(page, ui, expect_):
    _manager(ui, page)
    ui.register_equipment("AB-0001", "ノート PC")
    ui.register_equipment("AB-0002", "プロジェクター")
    page.once("dialog", lambda dialog: dialog.accept())
    page.locator('tr[data-equipment-number="AB-0002"]').get_by_role("button", name="削除").click()
    expect(page.locator('tr[data-equipment-number="AB-0002"]')).to_have_count(0)
