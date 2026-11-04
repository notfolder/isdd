"""段 2・3 の既存機能の変更（取りこぼしの検出）。段 2: 社員番号 7 桁。段 3: 「担当者」→「管理者」の改称。"""

import pytest
from playwright.sync_api import expect

from support.config import BTN_MAKE_STAFF, BTN_UNMAKE_STAFF, EMP_FORMAT_MSG, LAST_STAFF, OLD_ROLE, ROLE, STAFF_ONLY, emp
from support.ui import account_row, expect_url, field_error, login, messages, register

STAFF = {"number": emp("1"), "name": "担当太郎", "staff": True}
EMPLOYEE = {"number": emp("2"), "name": "社員花子"}


@pytest.mark.stage2
def test_employee_number_rule_changed_everywhere(app, page):
    """登録の検査（旧 6 桁は拒否、文言は新しい桁数）、ログイン、貸出の選択肢の表示がすべて新しい桁数になっている"""
    app.seed({"accounts": [STAFF, EMPLOYEE], "equipment": [{"number": "PC-001", "name": "ノートパソコン"}]})
    register(page, app.base_url, "000009", "旧桁数の人")
    expect(field_error(page, "id_employee_number")).to_have_text(EMP_FORMAT_MSG)
    register(page, app.base_url, emp("9"), "新桁数の人")
    expect_url(page, app.base_url, "/login/")
    login(page, app.base_url, emp("9"))
    expect(page.locator(".current-user")).to_have_text("新桁数の人")
    page.get_by_role("button", name="ログアウト").click()
    login(page, app.base_url, emp("1"))
    page.locator('tr[data-equipment-number="PC-001"]').get_by_role("button", name="貸出").click()
    expect(page.locator("#id_borrower option", has_text=f"社員花子（{emp('2')}）")).to_have_count(1)
    expect(page.locator("#id_borrower option", has_text="（000002）")).to_have_count(0)


@pytest.mark.stage3
def test_role_renamed_everywhere(app, page):
    """「担当者」の文言が、拒否の知らせ・一覧の列・ボタン・最後の 1 人の知らせのすべてで新しい名称になっている"""
    app.seed({"accounts": [STAFF, EMPLOYEE]})
    login(page, app.base_url, emp("2"))
    page.goto(f"{app.base_url}/accounts/")
    expect(messages(page)).to_have_text([STAFF_ONLY])
    page.get_by_role("button", name="ログアウト").click()
    login(page, app.base_url, emp("1"))
    page.goto(f"{app.base_url}/accounts/")
    expect(account_row(page, emp("1")).locator("td").nth(2)).to_have_text(ROLE)
    expect(account_row(page, emp("2")).get_by_role("button", name=BTN_MAKE_STAFF)).to_have_count(1)
    expect(account_row(page, emp("1")).get_by_role("button", name=BTN_UNMAKE_STAFF)).to_have_count(1)
    expect(page.get_by_text(OLD_ROLE, exact=False)).to_have_count(0)
    page.once("dialog", lambda d: d.accept())
    account_row(page, emp("1")).get_by_role("button", name=BTN_UNMAKE_STAFF).click()
    expect(messages(page)).to_have_text([LAST_STAFF])
