"""貸出と返却の E2E。"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from playwright.sync_api import expect

from helpers import create_equipment, go_status, lend_from_status, login, register, row, today_jst


def _manager(page, server):
    register(page, server, "100001", "山田 太郎")
    login(page, server, "100001")


def test_lend_equipment(server, page):
    _manager(page, server)
    create_equipment(page, server, "EQ-0001", "ノート PC 14 インチ")
    go_status(page, server)
    row(page, "EQ-0001").get_by_role("button", name="貸出", exact=True).click()
    expect(page).to_have_url(server.url("/lendings/new/?equipment=1"))
    expect(page.locator("#id_lent_on")).to_have_value(today_jst())
    page.select_option("#id_borrower", label="山田 太郎（100001）")
    page.get_by_role("button", name="登録", exact=True).click()
    expect(page).to_have_url(server.url("/"))
    expect(page.locator(".message")).to_have_text("貸出を登録しました")
    lent = row(page, "EQ-0001")
    expect(lent.locator("td").nth(2)).to_have_text("貸出中")
    expect(lent.locator("td").nth(3)).to_have_text("山田 太郎")
    expect(lent.locator("td").nth(4)).to_have_text(today_jst())


def test_reject_invalid_lending(server, page):
    _manager(page, server)
    create_equipment(page, server, "EQ-0001", "ノート PC 14 インチ")
    lend_from_status(page, server, "EQ-0001", "山田 太郎（100001）", today_jst())
    create_equipment(page, server, "EQ-0003", "モニター")

    go_status(page, server)
    row(page, "EQ-0003").get_by_role("button", name="貸出", exact=True).click()
    page.get_by_role("button", name="登録", exact=True).click()
    expect(page.locator(".field:has(#id_borrower) .field-error")).to_be_visible()

    tomorrow = (datetime.now(ZoneInfo("Asia/Tokyo")).date() + timedelta(days=1)).isoformat()
    page.locator("#id_lent_on").fill(tomorrow)
    page.select_option("#id_borrower", label="山田 太郎（100001）")
    page.get_by_role("button", name="登録", exact=True).click()
    expect(page.locator(".field:has(#id_lent_on) .field-error")).to_be_visible()
    expect(page.locator("#id_lent_on")).to_have_value(tomorrow)

    go_status(page, server)
    return_form = row(page, "EQ-0001").locator('form[action*="/return/"]')
    action = return_form.get_attribute("action")
    equipment_id = action.rstrip("/").split("/")[-2]
    page.goto(server.url(f"/lendings/new/?equipment={equipment_id}"))
    page.select_option("#id_borrower", label="山田 太郎（100001）")
    page.get_by_role("button", name="登録", exact=True).click()
    expect(page.locator(".error")).to_have_text("この備品は既に貸し出されています")
    go_status(page, server)
    expect(row(page, "EQ-0001").locator("td").nth(4)).to_have_text(today_jst())


def test_return_equipment(server, page):
    _manager(page, server)
    create_equipment(page, server, "EQ-0001", "ノート PC 14 インチ")
    lend_from_status(page, server, "EQ-0001", "山田 太郎（100001）", today_jst())
    go_status(page, server)
    page.once("dialog", lambda dialog: dialog.accept())
    row(page, "EQ-0001").get_by_role("button", name="返却", exact=True).click()
    expect(page.locator(".message")).to_have_text("返却を記録しました")
    returned = row(page, "EQ-0001")
    expect(returned.locator("td").nth(2)).to_have_text("空き")
    expect(returned.locator("td").nth(3)).to_have_text("")
    expect(returned.locator("td").nth(4)).to_have_text("")
