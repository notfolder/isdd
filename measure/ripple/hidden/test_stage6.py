"""段 6: 退職した人のアカウント。依頼の「削除した人と同じ扱い」から決まること（ログインできない、借りる社員の候補に出ない、
借りている社員と最後の管理者は退職にできない、退職した管理者は管理者の人数に数えない）と、社員番号を使い回さないことを見る。"""

import pytest
from playwright.sync_api import expect

from support.config import BTN_UNMAKE_STAFF, LAST_STAFF, emp
from support.ui import account_row, click_with_dialog, equipment_row, field_error, login, messages, register

ADMIN = {"number": emp("1"), "name": "管理太郎", "staff": True}
ADMIN2 = {"number": emp("2"), "name": "管理次郎", "staff": True}
EMP_A = {"number": emp("3"), "name": "社員花子"}
EMP_B = {"number": emp("4"), "name": "社員三郎"}
PC = [{"number": "PC-001", "name": "ノートパソコン"}]
RETIRE = "退職にする"


def role_cell(page, number):
    return account_row(page, number).locator("td").nth(2)


def retire(page, base_url, number):
    page.goto(f"{base_url}/accounts/")
    click_with_dialog(page, account_row(page, number).get_by_role("button", name=RETIRE), True)
    page.wait_for_load_state()
    page.goto(f"{base_url}/accounts/")


def logout(page, base_url):
    page.goto(base_url)
    page.get_by_role("button", name="ログアウト").click()


@pytest.mark.stage6
def test_retired_account_stays_and_cannot_login(app, page):
    app.seed({"accounts": [ADMIN, EMP_A, EMP_B]})
    login(page, app.base_url, emp("1"))
    retire(page, app.base_url, emp("3"))
    expect(role_cell(page, emp("3"))).to_have_text("退職")
    expect(role_cell(page, emp("4"))).to_have_text("社員")
    logout(page, app.base_url)
    login(page, app.base_url, emp("3"))
    expect(page.locator(".error")).to_have_text(["社員番号またはパスワードが違います"])
    expect(page.get_by_role("button", name="ログアウト")).to_have_count(0)
    register(page, app.base_url, emp("3"), "別の人")
    expect(field_error(page, "id_employee_number")).to_have_text("この社員番号は既に登録されています")


@pytest.mark.stage6
def test_retired_account_is_not_a_borrower_candidate(app, page):
    app.seed({"accounts": [ADMIN, EMP_A, EMP_B], "equipment": PC})
    login(page, app.base_url, emp("1"))
    retire(page, app.base_url, emp("3"))
    expect(role_cell(page, emp("3"))).to_have_text("退職")
    page.goto(app.base_url)
    equipment_row(page, "PC-001").get_by_role("button", name="貸出").click()
    expect(page.locator("#id_borrower option", has_text=f"社員三郎（{emp('4')}）")).to_have_count(1)
    expect(page.locator("#id_borrower option", has_text=f"（{emp('3')}）")).to_have_count(0)


@pytest.mark.stage6
def test_borrower_cannot_be_retired(app, page):
    """備品を借りている社員は、削除できないのと同じく退職にもできない"""
    app.seed({"accounts": [ADMIN, EMP_A], "equipment": PC,
              "lendings": [{"equipment": "PC-001", "borrower": emp("3"), "lent_on": "2025-01-06"}]})
    login(page, app.base_url, emp("1"))
    retire(page, app.base_url, emp("3"))
    expect(role_cell(page, emp("3"))).to_have_text("社員")
    logout(page, app.base_url)
    login(page, app.base_url, emp("3"))
    expect(page.locator(".current-user")).to_have_text("社員花子")


@pytest.mark.stage6
def test_last_admin_cannot_be_retired(app, page):
    app.seed({"accounts": [ADMIN, EMP_A]})
    login(page, app.base_url, emp("1"))
    retire(page, app.base_url, emp("1"))
    expect(role_cell(page, emp("1"))).to_have_text("管理者")
    expect(page.locator(".current-user")).to_have_text("管理太郎")


@pytest.mark.stage6
def test_retired_admin_is_not_counted_as_admin(app, page):
    """管理者 2 人のうち 1 人を退職にしたあと、残りの 1 人を管理者から外せない"""
    app.seed({"accounts": [ADMIN, ADMIN2, EMP_A]})
    login(page, app.base_url, emp("1"))
    retire(page, app.base_url, emp("2"))
    expect(role_cell(page, emp("2"))).to_have_text("退職")
    click_with_dialog(page, account_row(page, emp("1")).get_by_role("button", name=BTN_UNMAKE_STAFF), True)
    expect(messages(page)).to_have_text([LAST_STAFF])
    page.goto(f"{app.base_url}/accounts/")
    expect(role_cell(page, emp("1"))).to_have_text("管理者")
