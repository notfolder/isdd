"""段 1〜3: 備品の登録・修正・同時の修正・削除。"""

import pytest
from playwright.sync_api import expect

from support.ui import expect_url, click_with_dialog, equipment_row, field_error, login, messages
from support.config import BTN_MAKE_STAFF, BTN_UNMAKE_STAFF, EMP_FORMAT_MSG, LAST_STAFF, OLD_ROLE, ROLE, STAFF_ONLY, emp

STAFF = {"number": emp("1"), "name": "担当太郎", "staff": True}
STAFF_Y = {"number": emp("3"), "name": "担当次郎", "staff": True}
EMPLOYEE = {"number": emp("2"), "name": "社員花子"}
FORMAT_MESSAGE = "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください"


def fill_equipment(page, number, name):
    page.fill("#id_equipment_number", number)
    page.fill("#id_name", name)
    page.get_by_role("button", name="保存").click()


@pytest.mark.stage1
def test_equipment_create(app, page):
    app.seed({"accounts": [STAFF], "equipment": [{"number": "PC-001", "name": "ノートパソコン"}]})
    login(page, app.base_url, emp("1"))
    page.goto(f"{app.base_url}/equipment/new/")
    cases = [
        ("ＰＣ－００２", "ノートパソコン", "id_equipment_number", FORMAT_MESSAGE),
        ("A" * 21, "ノートパソコン", "id_equipment_number", FORMAT_MESSAGE),
        ("PC-001", "ノートパソコン", "id_equipment_number", "この管理番号は既に使われています"),
        ("PC-002", "あ" * 51, "id_name", "備品名は 50 文字以内で入力してください"),
    ]
    for number, name, input_id, message in cases:
        fill_equipment(page, number, name)
        expect(field_error(page, input_id)).to_have_text(message)
        expect(page.locator("#id_equipment_number")).to_have_value(number)
        expect(page.locator("#id_name")).to_have_value(name)
    fill_equipment(page, "PC-002", "ノートパソコン")
    expect_url(page, app.base_url, "/")
    expect(equipment_row(page, "PC-002")).to_contain_text("空き")


@pytest.mark.stage1
def test_equipment_update_and_delete_without_lending(app, page):
    app.seed({"accounts": [STAFF], "equipment": [{"number": "PC-001", "name": "ノートパソコン"}, {"number": "PC-002", "name": "モニター"}]})
    login(page, app.base_url, emp("1"))
    equipment_row(page, "PC-001").get_by_role("button", name="修正").click()
    fill_equipment(page, "PC-101", "ノートパソコン（新）")
    expect(equipment_row(page, "PC-101")).to_contain_text("ノートパソコン（新）")
    equipment_row(page, "PC-002").get_by_role("button", name="修正").click()
    fill_equipment(page, "PC-101", "モニター")
    expect(field_error(page, "id_equipment_number")).to_have_text("この管理番号は既に使われています")
    page.goto(app.base_url)
    delete_pc2 = equipment_row(page, "PC-002").get_by_role("button", name="削除")
    click_with_dialog(page, delete_pc2, accept=False)
    expect(equipment_row(page, "PC-002")).to_have_count(1)
    click_with_dialog(page, delete_pc2, accept=True)
    expect(equipment_row(page, "PC-002")).to_have_count(0)


@pytest.mark.stage2
def test_equipment_update_keeps_lending(app, page):
    app.seed({
        "accounts": [STAFF, EMPLOYEE],
        "equipment": [{"number": "PC-001", "name": "ノートパソコン"}, {"number": "PC-002", "name": "ノートパソコン"}],
        "lendings": [{"equipment": "PC-001", "borrower": emp("2"), "lent_on": "2026-10-01"}],
    })
    login(page, app.base_url, emp("1"))
    equipment_row(page, "PC-001").get_by_role("button", name="修正").click()
    fill_equipment(page, "PC-101", "ノートパソコン（新）")
    row = equipment_row(page, "PC-101")
    expect(row).to_contain_text("ノートパソコン（新）")
    expect(row).to_contain_text("貸出中")
    expect(row).to_contain_text("社員花子")


@pytest.mark.stage3
def test_stale_equipment_update(app, page, new_page):
    app.seed({
        "accounts": [STAFF, STAFF_Y],
        "equipment": [{"number": "PC-001", "name": "ノートパソコン"}, {"number": "PC-002", "name": "モニター"}],
    })
    page_y = new_page()
    login(page, app.base_url, emp("1"))
    login(page_y, app.base_url, emp("3"))
    for p in (page, page_y):
        equipment_row(p, "PC-001").get_by_role("button", name="修正").click()
    fill_equipment(page, "PC-001", "X が直した名前")
    expect_url(page, app.base_url, "/")
    fill_equipment(page_y, "PC-001", "Y が直した名前")
    stale = f"他の{ROLE}が先にこの備品を更新しました。貸出状況の画面から開き直してください"
    expect(page_y.locator(".error")).to_have_text([stale])
    page.reload()
    expect(equipment_row(page, "PC-001")).to_contain_text("X が直した名前")

    equipment_row(page, "PC-002").get_by_role("button", name="修正").click()
    page_y.goto(app.base_url)
    click_with_dialog(page_y, equipment_row(page_y, "PC-002").get_by_role("button", name="削除"), accept=True)
    expect(equipment_row(page_y, "PC-002")).to_have_count(0)
    fill_equipment(page, "PC-002", "消された備品")
    expect(page.locator(".error")).to_have_text([stale])
    page.goto(app.base_url)
    expect(page.locator("tbody tr")).to_have_count(1)
    expect(equipment_row(page, "PC-001")).to_have_count(1)


@pytest.mark.stage2
def test_equipment_delete_rejects_lent(app, page):
    app.seed({
        "accounts": [STAFF, EMPLOYEE],
        "equipment": [{"number": "PC-001", "name": "ノートパソコン"}, {"number": "PC-002", "name": "ノートパソコン"}],
        "lendings": [{"equipment": "PC-001", "borrower": emp("2"), "lent_on": "2026-10-01"}],
    })
    login(page, app.base_url, emp("1"))
    click_with_dialog(page, equipment_row(page, "PC-002").get_by_role("button", name="削除"), accept=True)
    expect(equipment_row(page, "PC-002")).to_have_count(0)
    click_with_dialog(page, equipment_row(page, "PC-001").get_by_role("button", name="削除"), accept=True)
    expect(messages(page)).to_have_text(["この備品は貸出中のため削除できません。先に返却を処理してください"])
    expect(equipment_row(page, "PC-001")).to_have_count(1)
