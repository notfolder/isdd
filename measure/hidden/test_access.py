"""段 3: 社員の制限・担当者の付け外し・パスワード再設定・アカウント削除。"""

import pytest
from playwright.sync_api import expect

from support.ui import expect_url, account_row, click_with_dialog, login, messages

STAFF = {"number": "000001", "name": "担当太郎", "staff": True}
EMPLOYEE_A = {"number": "000002", "name": "社員花子"}
EMPLOYEE_B = {"number": "000003", "name": "社員三郎"}
STAFF_ONLY = "この操作は担当者だけが行えます"
LAST_STAFF = "担当者が 1 人もいなくなるため、この操作はできません"


@pytest.mark.stage3
def test_employee_restrictions(app, page):
    app.seed({
        "accounts": [STAFF, EMPLOYEE_A],
        "equipment": [{"number": "PC-001", "name": "ノートパソコン"}, {"number": "PC-002", "name": "モニター"}],
        "lendings": [{"equipment": "PC-001", "borrower": "000002", "lent_on": "2026-10-01"}],
    })
    login(page, app.base_url, "000002")
    expect(page.get_by_role("button", name="修正")).to_have_count(0)
    expect(page.get_by_role("button", name="貸出")).to_have_count(0)
    expect(page.get_by_role("button", name="返却")).to_have_count(0)
    expect(page.get_by_role("link", name="アカウントの一覧")).to_have_count(0)
    for url in ["/equipment/new/", "/accounts/"]:
        page.goto(app.base_url + url)
        expect_url(page, app.base_url, "/")
        expect(messages(page)).to_have_text([STAFF_ONLY])
    page.get_by_role("button", name="ログアウト").click()
    for url in ["/equipment/new/", "/accounts/"]:
        page.goto(app.base_url + url)
        expect_url(page, app.base_url, "/login/")


@pytest.mark.stage3
def test_staff_role_change(app, page, new_page):
    app.seed({"accounts": [STAFF, EMPLOYEE_A]})
    login(page, app.base_url, "000001")
    page.get_by_role("link", name="アカウントの一覧").click()
    click_with_dialog(page, account_row(page, "000001").get_by_role("button", name="担当者から外す"), accept=True)
    expect(messages(page)).to_have_text([LAST_STAFF])
    click_with_dialog(page, account_row(page, "000002").get_by_role("button", name="担当者にする"), accept=True)
    expect(account_row(page, "000002")).to_contain_text("担当者")
    page_a = new_page()
    login(page_a, app.base_url, "000002")
    page_a.goto(f"{app.base_url}/equipment/new/")
    expect(page_a.locator("#id_equipment_number")).to_be_visible()
    click_with_dialog(page, account_row(page, "000002").get_by_role("button", name="担当者から外す"), accept=True)
    expect(account_row(page, "000002").locator("td").nth(2)).to_have_text("社員")


@pytest.mark.stage3
def test_password_reset(app, page, new_page):
    app.seed({"accounts": [STAFF, EMPLOYEE_A]})
    login(page, app.base_url, "000001")
    page.get_by_role("link", name="アカウントの一覧").click()
    row = account_row(page, "000002")
    row.get_by_text("パスワード再設定").click()
    row.locator("input[name=new_password]").fill("a" * 7)
    row.get_by_role("button", name="確定").click()
    row = account_row(page, "000002")
    expect(row.locator(".field-error")).to_have_text("パスワードは 8 文字以上で入力してください")
    row.locator("input[name=new_password]").fill("newpassword")
    row.get_by_role("button", name="確定").click()
    expect_url(page, app.base_url, "/accounts/")
    page_a = new_page()
    login(page_a, app.base_url, "000002", "password1")
    expect(page_a.locator(".error")).to_have_text(["社員番号またはパスワードが違います"])
    login(page_a, app.base_url, "000002", "newpassword")
    expect(page_a.locator(".current-user")).to_have_text("社員花子")


@pytest.mark.stage3
def test_account_delete(app, page, new_page):
    app.seed({
        "accounts": [STAFF, EMPLOYEE_A, EMPLOYEE_B],
        "equipment": [{"number": "PC-001", "name": "ノートパソコン"}, {"number": "PC-002", "name": "モニター"}],
        "lendings": [{"equipment": "PC-001", "borrower": "000002", "lent_on": "2026-10-01"}],
    })
    login(page, app.base_url, "000001")
    page.get_by_role("link", name="アカウントの一覧").click()
    click_with_dialog(page, account_row(page, "000003").get_by_role("button", name="削除"), accept=True)
    expect(account_row(page, "000003")).to_have_count(0)
    click_with_dialog(page, account_row(page, "000002").get_by_role("button", name="削除"), accept=True)
    expect(messages(page)).to_have_text(["この社員は備品を借りているため削除できません。先に返却を処理してください"])
    click_with_dialog(page, account_row(page, "000001").get_by_role("button", name="削除"), accept=True)
    expect(messages(page)).to_have_text([LAST_STAFF])
    page_b = new_page()
    login(page_b, app.base_url, "000003")
    expect(page_b.locator(".error")).to_have_text(["社員番号またはパスワードが違います"])
    page.goto(app.base_url)
    page.locator('tr[data-equipment-number="PC-002"]').get_by_role("button", name="貸出").click()
    options = page.locator("#id_borrower option").all_inner_texts()
    assert "社員三郎（000003）" not in options
    assert "社員花子（000002）" in options
