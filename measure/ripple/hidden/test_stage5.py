"""段 5: 修理中の備品。依頼の「貸し出せない」「貸出中は返却してから修理に出す」が、
画面を開いたままの操作（開いたあとに状態が変わった）でも守られているか、管理者以外に操作を出していないかを見る。"""

import pytest
from playwright.sync_api import expect

from helpers import borrower_cell, click_any_dialog, status_cell
from support.config import emp
from support.ui import click_with_dialog, equipment_row, login

ADMIN = {"number": emp("1"), "name": "管理太郎", "staff": True}
EMP_A = {"number": emp("3"), "name": "社員花子"}
PCS = [{"number": f"PC-00{i}", "name": f"ノートパソコン {i}"} for i in (1, 2)]
TO_REPAIR = "修理に出す"
FROM_REPAIR = "修理から戻す"


def send_to_repair(page, number):
    click_any_dialog(page, equipment_row(page, number).get_by_role("button", name=TO_REPAIR))


@pytest.mark.stage5
def test_repair_cycle(app, page, new_page):
    app.seed({"accounts": [ADMIN, EMP_A], "equipment": PCS[:1]})
    login(page, app.base_url, emp("1"))
    send_to_repair(page, "PC-001")
    page.goto(app.base_url)
    row = equipment_row(page, "PC-001")
    expect(status_cell(row)).to_have_text("修理中")
    expect(row.get_by_role("button", name="貸出")).to_have_count(0)
    anonymous = new_page()
    anonymous.goto(app.base_url)
    expect(status_cell(equipment_row(anonymous, "PC-001"))).to_have_text("修理中")
    click_any_dialog(page, row.get_by_role("button", name=FROM_REPAIR))
    page.goto(app.base_url)
    expect(status_cell(row)).to_have_text("空き")
    row.get_by_role("button", name="貸出").click()
    page.select_option("#id_borrower", label=f"社員花子（{emp('3')}）")
    page.get_by_role("button", name="登録").click()
    expect(status_cell(equipment_row(page, "PC-001"))).to_have_text("貸出中")


@pytest.mark.stage5
def test_cannot_lend_after_sent_to_repair(app, page, new_page):
    """貸出の登録画面を開いたあとに修理に出された備品は、登録を押しても貸し出されない"""
    app.seed({"accounts": [ADMIN, EMP_A], "equipment": PCS[:1]})
    login(page, app.base_url, emp("1"))
    equipment_row(page, "PC-001").get_by_role("button", name="貸出").click()
    page.locator("#id_borrower").wait_for()
    other = new_page()
    login(other, app.base_url, emp("1"))
    send_to_repair(other, "PC-001")
    other.goto(app.base_url)
    expect(status_cell(equipment_row(other, "PC-001"))).to_have_text("修理中")
    page.select_option("#id_borrower", label=f"社員花子（{emp('3')}）")
    page.get_by_role("button", name="登録").click()
    page.wait_for_load_state()
    page.goto(app.base_url)
    row = equipment_row(page, "PC-001")
    expect(status_cell(row)).to_have_text("修理中")
    expect(borrower_cell(row)).to_have_text("")


@pytest.mark.stage5
def test_lent_equipment_cannot_be_sent_to_repair(app, page, new_page):
    """貸出中の備品には「修理に出す」を出さず、画面を開いたあとに貸し出された備品も修理中にならない"""
    app.seed({"accounts": [ADMIN, EMP_A], "equipment": PCS,
              "lendings": [{"equipment": "PC-001", "borrower": emp("3"), "lent_on": "2025-01-06"}]})
    login(page, app.base_url, emp("1"))
    expect(equipment_row(page, "PC-002").get_by_role("button", name=TO_REPAIR)).to_have_count(1)
    expect(equipment_row(page, "PC-001").get_by_role("button", name=TO_REPAIR)).to_have_count(0)
    other = new_page()
    login(other, app.base_url, emp("1"))
    equipment_row(other, "PC-002").get_by_role("button", name="貸出").click()
    other.select_option("#id_borrower", label=f"社員花子（{emp('3')}）")
    other.get_by_role("button", name="登録").click()
    expect(status_cell(equipment_row(other, "PC-002"))).to_have_text("貸出中")
    send_to_repair(page, "PC-002")
    page.goto(app.base_url)
    row = equipment_row(page, "PC-002")
    expect(status_cell(row)).to_have_text("貸出中")
    expect(borrower_cell(row)).to_have_text("社員花子")
    click_with_dialog(page, row.get_by_role("button", name="返却"), True)
    page.wait_for_load_state()
    page.goto(app.base_url)
    expect(status_cell(equipment_row(page, "PC-002"))).to_have_text("空き")


@pytest.mark.stage5
def test_repair_is_admin_only(app, page, new_page):
    """社員とログインしていない人には、修理の操作を出さない"""
    app.seed({"accounts": [ADMIN, EMP_A], "equipment": PCS})
    admin = new_page()
    login(admin, app.base_url, emp("1"))
    send_to_repair(admin, "PC-002")
    admin.goto(app.base_url)
    expect(status_cell(equipment_row(admin, "PC-002"))).to_have_text("修理中")
    page.goto(app.base_url)
    expect(equipment_row(page, "PC-001")).to_have_count(1)
    expect(page.get_by_role("button")).to_have_count(0)
    login(page, app.base_url, emp("3"))
    expect(equipment_row(page, "PC-001")).to_have_count(1)
    expect(page.get_by_role("button", name=TO_REPAIR)).to_have_count(0)
    expect(page.get_by_role("button", name=FROM_REPAIR)).to_have_count(0)
