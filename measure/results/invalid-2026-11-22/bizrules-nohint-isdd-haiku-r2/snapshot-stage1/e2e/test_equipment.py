"""備品の登録・修正・削除の E2E。"""

from playwright.sync_api import expect

from helpers import create_equipment, go_status, lend_from_status, login, register, row, today_jst


def _manager(page, server):
    register(page, server, "100001", "山田 太郎")
    login(page, server, "100001")


def test_register_equipment(server, page):
    _manager(page, server)
    go_status(page, server)
    page.get_by_role("link", name="備品を登録").click()
    page.locator("#id_equipment_number").fill("EQ-0001")
    page.locator("#id_name").fill("ノート PC 14 インチ")
    page.get_by_role("button", name="保存", exact=True).click()
    expect(page).to_have_url(server.url("/"))
    expect(page.locator(".message")).to_have_text("備品を登録しました")
    expect(row(page, "EQ-0001").locator("td").nth(2)).to_have_text("空き")


def test_reject_invalid_equipment(server, page):
    _manager(page, server)
    create_equipment(page, server, "EQ-0001", "ノート PC")
    page.goto(server.url("/equipment/new/"))
    page.locator("#id_equipment_number").fill("EQ 0002")
    page.locator("#id_name").fill("")
    page.get_by_role("button", name="保存", exact=True).click()
    expect(page.locator(".field:has(#id_equipment_number) .field-error")).to_be_visible()
    expect(page.locator(".field:has(#id_name) .field-error")).to_be_visible()
    expect(page.locator("#id_equipment_number")).to_have_value("EQ 0002")

    page.locator("#id_equipment_number").fill("EQ-0001")
    page.locator("#id_name").fill("マウス")
    page.get_by_role("button", name="保存", exact=True).click()
    expect(page.locator(".field:has(#id_equipment_number) .field-error")).to_have_text(
        "この管理番号は登録されています")
    expect(page.locator("#id_equipment_number")).to_have_value("EQ-0001")
    go_status(page, server)
    expect(page.locator("tbody tr")).to_have_count(1)


def test_edit_equipment(server, page):
    _manager(page, server)
    create_equipment(page, server, "EQ-0001", "ノート PC 14 インチ")
    go_status(page, server)
    row(page, "EQ-0001").get_by_role("button", name="修正", exact=True).click()
    page.locator("#id_equipment_number").fill("EQ-0002")
    page.locator("#id_name").fill("ノート PC 16 インチ")
    page.get_by_role("button", name="保存", exact=True).click()
    expect(page.locator(".message")).to_have_text("備品を修正しました")
    expect(row(page, "EQ-0002").locator("td").nth(1)).to_have_text("ノート PC 16 インチ")
    expect(page.locator('tbody tr[data-equipment-number="EQ-0001"]')).to_have_count(0)


def test_delete_equipment(server, page):
    _manager(page, server)
    create_equipment(page, server, "EQ-0002", "マウス")
    go_status(page, server)
    page.once("dialog", lambda dialog: dialog.accept())
    row(page, "EQ-0002").get_by_role("button", name="削除", exact=True).click()
    expect(page.locator(".message")).to_have_text("備品を削除しました")
    expect(page.locator('tbody tr[data-equipment-number="EQ-0002"]')).to_have_count(0)


def test_refuse_delete_lent(server, page):
    _manager(page, server)
    create_equipment(page, server, "EQ-0001", "ノート PC 14 インチ")
    lend_from_status(page, server, "EQ-0001", "山田 太郎（100001）", today_jst())
    go_status(page, server)
    page.once("dialog", lambda dialog: dialog.accept())
    row(page, "EQ-0001").get_by_role("button", name="削除", exact=True).click()
    expect(page.locator(".error")).to_have_text("貸出中の備品は削除できません")
    expect(row(page, "EQ-0001")).to_have_count(1)
    expect(row(page, "EQ-0001").locator("td").nth(2)).to_have_text("貸出中")
