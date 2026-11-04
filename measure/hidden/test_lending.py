"""段 1〜3: 貸出・同時の貸出・返却・ログインしない閲覧。"""

import datetime
from zoneinfo import ZoneInfo

import pytest
from playwright.sync_api import expect

from support.ui import expect_url, click_with_dialog, equipment_row, field_error, login, messages

STAFF = {"number": "000001", "name": "担当太郎", "staff": True}
STAFF_Y = {"number": "000003", "name": "担当次郎", "staff": True}
EMPLOYEE_A = {"number": "000002", "name": "社員花子"}
EMPLOYEE_B = {"number": "000004", "name": "社員三郎"}


def today() -> datetime.date:
    return datetime.datetime.now(ZoneInfo("Asia/Tokyo")).date()


def submit_lending(page, borrower_label, lent_on):
    if borrower_label is not None:
        page.select_option("#id_borrower", label=borrower_label)
    if lent_on is not None:
        page.fill("#id_lent_on", lent_on.isoformat())
    page.get_by_role("button", name="登録").click()


@pytest.mark.stage2
def test_lending(app, page):
    app.seed({
        "accounts": [STAFF, EMPLOYEE_A],
        "equipment": [{"number": "PC-001", "name": "ノートパソコン"}, {"number": "PC-002", "name": "モニター"}],
    })
    login(page, app.base_url, "000001")
    equipment_row(page, "PC-001").get_by_role("button", name="貸出").click()
    expect(page.locator(".lending-equipment")).to_have_text("備品: PC-001 ノートパソコン")
    expect(page.locator("#id_lent_on")).to_have_value(today().isoformat())
    expect(page.locator("#id_borrower option", has_text="社員花子（000002）")).to_have_count(1)
    submit_lending(page, None, None)
    expect(field_error(page, "id_borrower")).to_have_text("借りる社員を選んでください")
    submit_lending(page, "社員花子（000002）", today() + datetime.timedelta(days=1))
    expect(field_error(page, "id_lent_on")).to_have_text("貸出日に未来の日付は入力できません")
    submit_lending(page, "社員花子（000002）", today())
    expect_url(page, app.base_url, "/")
    past = today() - datetime.timedelta(days=30)
    equipment_row(page, "PC-002").get_by_role("button", name="貸出").click()
    submit_lending(page, "社員花子（000002）", past)
    page.get_by_role("button", name="ログアウト").click()
    for number, day in [("PC-001", today()), ("PC-002", past)]:
        row = equipment_row(page, number)
        expect(row).to_contain_text("貸出中")
        expect(row).to_contain_text("社員花子")
        expect(row).to_contain_text(day.isoformat())


@pytest.mark.stage3
def test_concurrent_lending(app, page, new_page):
    app.seed({
        "accounts": [STAFF, STAFF_Y, EMPLOYEE_A, EMPLOYEE_B],
        "equipment": [{"number": "PC-001", "name": "ノートパソコン"}],
    })
    page_y = new_page()
    login(page, app.base_url, "000001")
    login(page_y, app.base_url, "000003")
    for p in (page, page_y):
        equipment_row(p, "PC-001").get_by_role("button", name="貸出").click()
    submit_lending(page, "社員花子（000002）", None)
    expect_url(page, app.base_url, "/")
    submit_lending(page_y, "社員三郎（000004）", None)
    expect(messages(page_y)).to_have_text(["この備品は既に貸出中です"])
    expect(equipment_row(page_y, "PC-001")).to_contain_text("社員花子")


@pytest.mark.stage2
def test_return(app, page):
    app.seed({
        "accounts": [STAFF, EMPLOYEE_A],
        "equipment": [{"number": "PC-001", "name": "ノートパソコン"}],
        "lendings": [{"equipment": "PC-001", "borrower": "000002", "lent_on": "2026-10-01"}],
    })
    login(page, app.base_url, "000001")
    return_x = equipment_row(page, "PC-001").get_by_role("button", name="返却")
    click_with_dialog(page, return_x, accept=False)
    expect(equipment_row(page, "PC-001")).to_contain_text("貸出中")
    click_with_dialog(page, return_x, accept=True)
    row = equipment_row(page, "PC-001")
    expect(row).to_contain_text("空き")
    expect(row).not_to_contain_text("社員花子")
    expect(row).not_to_contain_text("2026-10-01")


@pytest.mark.stage3
def test_duplicate_return(app, page, new_page):
    app.seed({
        "accounts": [STAFF, STAFF_Y, EMPLOYEE_A],
        "equipment": [{"number": "PC-001", "name": "ノートパソコン"}],
        "lendings": [{"equipment": "PC-001", "borrower": "000002", "lent_on": "2026-10-01"}],
    })
    page_y = new_page()
    login(page, app.base_url, "000001")
    login(page_y, app.base_url, "000003")
    click_with_dialog(page, equipment_row(page, "PC-001").get_by_role("button", name="返却"), accept=True)
    expect(equipment_row(page, "PC-001")).to_contain_text("空き")
    click_with_dialog(page_y, equipment_row(page_y, "PC-001").get_by_role("button", name="返却"), accept=True)
    expect(messages(page_y)).to_have_text(["この備品は既に返却されています"])


@pytest.mark.stage2
def test_lending_status_without_login(app, page):
    app.seed({
        "accounts": [STAFF, EMPLOYEE_A],
        "equipment": [
            {"number": "PC-003", "name": "マウス"},
            {"number": "PC-001", "name": "ノートパソコン"},
            {"number": "PC-002", "name": "モニター"},
        ],
        "lendings": [{"equipment": "PC-002", "borrower": "000002", "lent_on": "2026-10-01"}],
    })
    page.goto(app.base_url)
    rows = page.locator("tbody tr")
    expect(rows).to_have_count(3)
    expect(rows.nth(0)).to_contain_text("PC-001")
    expect(rows.nth(1)).to_contain_text("PC-002")
    expect(rows.nth(2)).to_contain_text("PC-003")
    expect(rows.nth(1)).to_contain_text("社員花子")
    expect(rows.nth(1)).to_contain_text("2026-10-01")
    expect(rows.nth(0)).to_contain_text("空き")
    expect(rows.nth(2)).to_contain_text("空き")
    expect(page.get_by_role("button")).to_have_count(0)
    expect(page.get_by_role("link", name="ログイン")).to_be_visible()
    expect(page.get_by_role("link", name="アカウント登録")).to_be_visible()


@pytest.mark.stage1
def test_lending_status_empty_and_sorted(app, page):
    page.goto(app.base_url)
    expect(page.get_by_text("備品は登録されていません")).to_be_visible()
    app.seed({"accounts": [STAFF], "equipment": [{"number": "PC-003", "name": "マウス"}, {"number": "PC-001", "name": "ノートパソコン"}]})
    page.goto(app.base_url)
    rows = page.locator("tbody tr")
    expect(rows).to_have_count(2)
    expect(rows.nth(0)).to_contain_text("PC-001")
    expect(rows.nth(1)).to_contain_text("PC-003")
    expect(rows.nth(0)).to_contain_text("空き")
    expect(page.get_by_role("button")).to_have_count(0)
