"""貸出と返却の E2E テスト（RQ-TS-LEND-EQUIPMENT、RQ-TS-RETURN-EQUIPMENT）。"""
import datetime

from playwright.sync_api import expect


def _manager_with_equipment(ui, page):
    ui.register("000001", "総務 太郎", "password123")
    page.wait_for_url("**/login/")
    ui.register("000002", "社員 花子", "password123")
    page.wait_for_url("**/login/")
    ui.login("000001", "password123")
    page.wait_for_url("**/")
    ui.register_equipment("AB-0001", "ノート PC")


def test_lend_equipment(page, ui, expect_):
    _manager_with_equipment(ui, page)
    row = page.locator('tr[data-equipment-number="AB-0001"]')
    row.get_by_role("button", name="貸出").click()
    page.select_option("#id_borrower", label="社員 花子（000002）")
    page.fill("#id_lent_on", (datetime.date.today() + datetime.timedelta(days=1)).isoformat())
    page.get_by_role("button", name="登録").click()
    expect(page.locator("#id_lent_on").locator("..").locator(".field-error")).to_be_visible()
    today = datetime.date.today().isoformat()
    page.fill("#id_lent_on", today)
    page.get_by_role("button", name="登録").click()
    page.wait_for_url("**/")
    expect(row).to_contain_text("貸出中")
    expect(row).to_contain_text("社員 花子")
    expect(row).to_contain_text(today)
    page.goto("/lendings/new/?equipment=AB-0001")
    expect(page.locator(".error")).to_have_text("この備品は貸出中です")


def test_return_equipment(page, ui, expect_):
    _manager_with_equipment(ui, page)
    row = page.locator('tr[data-equipment-number="AB-0001"]')
    row.get_by_role("button", name="貸出").click()
    page.select_option("#id_borrower", label="社員 花子（000002）")
    page.get_by_role("button", name="登録").click()
    page.wait_for_url("**/")
    expect(row.get_by_role("button", name="返却")).to_be_visible()
    page.once("dialog", lambda dialog: dialog.accept())
    row.get_by_role("button", name="返却").click()
    expect(row).to_contain_text("空き")
    expect(row.get_by_role("button", name="返却")).to_have_count(0)
    expect(row.get_by_role("button", name="貸出")).to_be_visible()
