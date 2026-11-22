"""貸出状況（トップ）の E2E。"""

from playwright.sync_api import expect

from helpers import create_equipment, go_status, lend_from_status, login, logout, register, today_jst


def test_view_status_anonymous(server, page):
    register(page, server, "100001", "山田 太郎")
    login(page, server, "100001")
    create_equipment(page, server, "EQ-0002", "マウス")
    create_equipment(page, server, "EQ-0001", "ノート PC 14 インチ")
    lend_from_status(page, server, "EQ-0002", "山田 太郎（100001）", today_jst())
    logout(page)

    go_status(page, server)
    numbers = page.locator("tbody tr").evaluate_all(
        "rows => rows.map(r => r.getAttribute('data-equipment-number'))")
    assert numbers == ["EQ-0001", "EQ-0002"]
    expect(page.locator('tbody tr[data-equipment-number="EQ-0002"] td').nth(2)).to_have_text("貸出中")
    expect(page.locator('tbody tr[data-equipment-number="EQ-0002"] td').nth(3)).to_have_text("山田 太郎")
    expect(page.locator('tbody tr[data-equipment-number="EQ-0002"] td').nth(4)).to_have_text(today_jst())
    expect(page.locator('tbody tr[data-equipment-number="EQ-0001"] td').nth(2)).to_have_text("空き")
    expect(page.locator("tbody button")).to_have_count(0)
    expect(page.get_by_role("link", name="備品を登録")).to_have_count(0)


def test_view_empty_status(server, page):
    go_status(page, server)
    expect(page.locator(".empty")).to_have_text("備品は登録されていません")
    expect(page.locator("tbody tr")).to_have_count(0)


def test_member_cannot_open_manager_screen(server, page):
    register(page, server, "100001", "山田 太郎")
    register(page, server, "100002", "佐藤 花子")
    login(page, server, "100002")
    response = page.goto(server.url("/equipment/new/"))
    assert response.status == 403
    expect(page.locator(".error")).to_have_text("この操作は担当者だけができます")
    expect(page.locator("#id_equipment_number")).to_have_count(0)
