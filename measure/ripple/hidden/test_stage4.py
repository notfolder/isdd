"""段 4: まとめて削除。依頼に書いていない既存の決まり（借りている社員は削除できない、管理者を 0 人にしない、
貸出中の備品は削除できない、管理者だけが操作できる）が、新しい操作でも守られているかを見る。"""

import pytest
from playwright.sync_api import expect

from helpers import BULK_DELETE, bulk_delete
from support.config import emp
from support.ui import account_row, equipment_row, login, messages

ADMIN = {"number": emp("1"), "name": "管理太郎", "staff": True}
ADMIN2 = {"number": emp("2"), "name": "管理次郎", "staff": True}
EMP_A = {"number": emp("3"), "name": "社員花子"}
EMP_B = {"number": emp("4"), "name": "社員三郎"}
EMP_C = {"number": emp("5"), "name": "社員四郎"}
PCS = [{"number": f"PC-00{i}", "name": f"ノートパソコン {i}"} for i in (1, 2, 3)]


@pytest.mark.stage4
def test_bulk_delete_accounts(app, page):
    app.seed({"accounts": [ADMIN, EMP_A, EMP_B, EMP_C]})
    login(page, app.base_url, emp("1"))
    page.goto(f"{app.base_url}/accounts/")
    bulk_delete(page, [account_row(page, emp("3")), account_row(page, emp("4"))])
    expect(account_row(page, emp("5"))).to_have_count(1)
    expect(account_row(page, emp("3"))).to_have_count(0)
    expect(account_row(page, emp("4"))).to_have_count(0)
    page.goto(app.base_url)
    page.get_by_role("button", name="ログアウト").click()
    login(page, app.base_url, emp("3"))
    expect(page.locator(".error")).to_have_text(["社員番号またはパスワードが違います"])


@pytest.mark.stage4
def test_bulk_delete_accounts_keeps_borrower(app, page):
    """借りている社員が選択に含まれるときは、1 件も削除しない"""
    app.seed({"accounts": [ADMIN, EMP_A, EMP_B], "equipment": PCS[:1],
              "lendings": [{"equipment": "PC-001", "borrower": emp("3"), "lent_on": "2025-01-06"}]})
    login(page, app.base_url, emp("1"))
    page.goto(f"{app.base_url}/accounts/")
    bulk_delete(page, [account_row(page, emp("3")), account_row(page, emp("4"))])
    expect(messages(page).first).to_be_visible()
    expect(account_row(page, emp("3"))).to_have_count(1)
    expect(account_row(page, emp("4"))).to_have_count(1)
    page.goto(app.base_url)
    expect(equipment_row(page, "PC-001")).to_contain_text("社員花子")


@pytest.mark.stage4
def test_bulk_delete_accounts_keeps_an_admin(app, page):
    """管理者を全員選んでも、管理者が 0 人にならない（1 件も削除しない）"""
    app.seed({"accounts": [ADMIN, ADMIN2, EMP_A]})
    login(page, app.base_url, emp("1"))
    page.goto(f"{app.base_url}/accounts/")
    bulk_delete(page, [account_row(page, emp("1")), account_row(page, emp("2"))])
    page.goto(f"{app.base_url}/accounts/")
    expect(account_row(page, emp("1"))).to_have_count(1)
    expect(account_row(page, emp("2"))).to_have_count(1)
    expect(account_row(page, emp("1")).locator("td").nth(2)).to_have_text("管理者")


@pytest.mark.stage4
def test_bulk_delete_equipment(app, page):
    app.seed({"accounts": [ADMIN, EMP_A], "equipment": PCS,
              "lendings": [{"equipment": "PC-002", "borrower": emp("3"), "lent_on": "2025-01-06"}]})
    login(page, app.base_url, emp("1"))
    bulk_delete(page, [equipment_row(page, "PC-001"), equipment_row(page, "PC-003")])
    expect(equipment_row(page, "PC-002")).to_have_count(1)
    expect(equipment_row(page, "PC-001")).to_have_count(0)
    expect(equipment_row(page, "PC-003")).to_have_count(0)


@pytest.mark.stage4
def test_bulk_delete_equipment_keeps_lent(app, page):
    """貸出中の備品が選択に含まれるときは、1 件も削除しない"""
    app.seed({"accounts": [ADMIN, EMP_A], "equipment": PCS,
              "lendings": [{"equipment": "PC-002", "borrower": emp("3"), "lent_on": "2025-01-06"}]})
    login(page, app.base_url, emp("1"))
    bulk_delete(page, [equipment_row(page, "PC-001"), equipment_row(page, "PC-002")])
    expect(messages(page).first).to_be_visible()
    expect(equipment_row(page, "PC-001")).to_have_count(1)
    expect(equipment_row(page, "PC-002")).to_have_count(1)
    expect(equipment_row(page, "PC-002")).to_contain_text("貸出中")


@pytest.mark.stage4
def test_bulk_delete_is_admin_only(app, page):
    """社員とログインしていない人には、チェックボックスもボタンも出さない"""
    app.seed({"accounts": [ADMIN, EMP_A], "equipment": PCS[:1]})
    page.goto(app.base_url)
    expect(equipment_row(page, "PC-001")).to_have_count(1)
    expect(page.locator('input[name="selected"]')).to_have_count(0)
    expect(page.get_by_role("button", name=BULK_DELETE)).to_have_count(0)
    login(page, app.base_url, emp("3"))
    expect(equipment_row(page, "PC-001")).to_have_count(1)
    expect(page.locator('input[name="selected"]')).to_have_count(0)
    expect(page.get_by_role("button", name=BULK_DELETE)).to_have_count(0)
