"""題材 bizrules: 基本の流れ 3 本と、依頼文に書いていない業務のきまり 8 本。

きまりのテストは文言を見ない。受け付けたか・受け付けなかったかを、貸出状況の一覧の状態で確かめる。
前提データは画面操作で入れる（support/seed.py）。日付は日本時間。
"""

import datetime
from zoneinfo import ZoneInfo

import pytest
from playwright.sync_api import expect

from support.ui import add_equipment, click_with_dialog, equipment_row, login, register, save_button

STAFF = {"number": "000001", "name": "担当太郎"}
EMP_A = {"number": "000002", "name": "社員花子"}
EMP_B = {"number": "000003", "name": "社員三郎"}
LABEL_A = "社員花子（000002）"
LABEL_B = "社員三郎（000003）"


def today() -> datetime.date:
    return datetime.datetime.now(ZoneInfo("Asia/Tokyo")).date()


def days_ago(n: int) -> str:
    return (today() - datetime.timedelta(days=n)).isoformat()


def pcs(n: int) -> list:
    return [{"number": f"PC-00{i}", "name": f"備品{i}"} for i in range(1, n + 1)]


def try_lend(page, base_url: str, number: str, label: str, lent_on=None) -> None:
    """担当者として貸出を試みる。受け付けられたかどうかは呼び出し側が一覧で確かめる。
    選択肢やボタンが無い作りでも落とさない（受け付けない作りの 1 つとして扱う）。"""
    page.goto(base_url)
    button = equipment_row(page, number).get_by_role("button", name="貸出")
    if button.count() == 0:
        return
    button.click()
    try:
        page.select_option("#id_borrower", label=label, timeout=3000)
    except Exception:
        return
    if lent_on is not None:
        page.fill("#id_lent_on", lent_on)
    page.get_by_role("button", name="登録", exact=True).click()
    page.wait_for_load_state()


def status_text(page, base_url: str, number: str) -> str:
    page.goto(base_url)
    return equipment_row(page, number).inner_text()


def lent(page, base_url: str, number: str) -> bool:
    """貸し出されているか（状態が「空き」でない）"""
    text = status_text(page, base_url, number)
    return "空き" not in text


# ---- 基本の流れ（きまりに関係なく通るはず） ----

@pytest.mark.stage1
def test_base_accounts_and_login(app, page):
    register(page, app.base_url, **{"number": STAFF["number"], "name": STAFF["name"]})
    expect(page.get_by_text("登録しました。ログインしてください")).to_be_visible()
    register(page, app.base_url, **{"number": EMP_A["number"], "name": EMP_A["name"]})
    login(page, app.base_url, STAFF["number"], "wrong-password")
    expect(page.locator(".error")).to_contain_text("社員番号またはパスワードが違います")
    login(page, app.base_url, STAFF["number"])
    expect(page.locator(".current-user")).to_contain_text("担当太郎")
    page.goto(app.base_url)
    expect(add_equipment(page)).to_be_visible()
    page.get_by_role("button", name="ログアウト").click()
    login(page, app.base_url, EMP_A["number"])
    page.goto(app.base_url)
    expect(add_equipment(page)).to_have_count(0)


@pytest.mark.stage1
def test_base_equipment(app, page):
    page.goto(app.base_url)
    expect(page.get_by_text("備品は登録されていません")).to_be_visible()
    app.seed({"accounts": [STAFF, EMP_A], "equipment": [{"number": "PC-003", "name": "マウス"}, {"number": "PC-001", "name": "ノートパソコン"}]})
    page.goto(app.base_url)
    rows = page.locator("tbody tr")
    expect(rows).to_have_count(2)
    expect(rows.nth(0)).to_contain_text("PC-001")
    expect(rows.nth(1)).to_contain_text("PC-003")
    expect(rows.nth(0)).to_contain_text("空き")
    expect(page.get_by_role("button")).to_have_count(0)
    login(page, app.base_url, STAFF["number"])
    page.goto(app.base_url)
    equipment_row(page, "PC-003").get_by_role("button", name="修正").click()
    page.fill("#id_name", "無線マウス")
    save_button(page).click()
    page.goto(app.base_url)
    expect(equipment_row(page, "PC-003")).to_contain_text("無線マウス")
    click_with_dialog(page, equipment_row(page, "PC-001").get_by_role("button", name="削除"), True)
    page.wait_for_load_state()
    page.goto(app.base_url)
    expect(page.locator("tbody tr")).to_have_count(1)


@pytest.mark.stage1
def test_base_lend_and_return(app, page):
    app.seed({"accounts": [STAFF, EMP_A], "equipment": pcs(1)})
    login(page, app.base_url, STAFF["number"])
    try_lend(page, app.base_url, "PC-001", LABEL_A)
    page.goto(app.base_url)
    row = equipment_row(page, "PC-001")
    expect(row).to_contain_text("貸出中")
    expect(row).to_contain_text("社員花子")
    expect(row).to_contain_text(today().isoformat())
    click_with_dialog(page, row.get_by_role("button", name="返却"), True)
    page.wait_for_load_state()
    page.goto(app.base_url)
    row = equipment_row(page, "PC-001")
    expect(row).to_contain_text("空き")
    expect(row).not_to_contain_text("社員花子")


# ---- 依頼文に書いていない業務のきまり ----

@pytest.mark.stage1
def test_rule_b1_two_items_per_person(app, page):
    app.seed({"accounts": [STAFF, EMP_A, EMP_B], "equipment": pcs(3)})
    login(page, app.base_url, STAFF["number"])
    try_lend(page, app.base_url, "PC-001", LABEL_A)
    try_lend(page, app.base_url, "PC-002", LABEL_A)
    assert lent(page, app.base_url, "PC-001") and lent(page, app.base_url, "PC-002"), "2 件目までは貸し出せる"
    try_lend(page, app.base_url, "PC-003", LABEL_A)
    assert not lent(page, app.base_url, "PC-003"), "3 件目は貸し出せない"
    try_lend(page, app.base_url, "PC-003", LABEL_B)
    assert lent(page, app.base_url, "PC-003"), "別の社員には貸し出せる"


@pytest.mark.stage1
def test_rule_b2_borrower_can_return(app, page, new_page):
    app.seed({"accounts": [STAFF, EMP_A, EMP_B], "equipment": pcs(1)})
    login(page, app.base_url, STAFF["number"])
    try_lend(page, app.base_url, "PC-001", LABEL_A)
    assert lent(page, app.base_url, "PC-001")
    other = new_page()
    login(other, app.base_url, EMP_B["number"])
    other.goto(app.base_url)
    expect(equipment_row(other, "PC-001").get_by_role("button", name="返却")).to_have_count(0)
    borrower = new_page()
    login(borrower, app.base_url, EMP_A["number"])
    borrower.goto(app.base_url)
    click_with_dialog(borrower, equipment_row(borrower, "PC-001").get_by_role("button", name="返却"), True)
    borrower.wait_for_load_state()
    assert not lent(page, app.base_url, "PC-001"), "借りている本人は返却できる"


@pytest.mark.stage1
def test_rule_b3_lent_on_within_30_days(app, page):
    app.seed({"accounts": [STAFF, EMP_A, EMP_B], "equipment": pcs(3)})
    login(page, app.base_url, STAFF["number"])
    try_lend(page, app.base_url, "PC-001", LABEL_A, days_ago(30))
    assert lent(page, app.base_url, "PC-001"), "30 日前の貸出日は受け付ける"
    assert days_ago(30) in status_text(page, app.base_url, "PC-001")
    try_lend(page, app.base_url, "PC-002", LABEL_B, days_ago(31))
    assert not lent(page, app.base_url, "PC-002"), "31 日前の貸出日は受け付けない"
    try_lend(page, app.base_url, "PC-003", LABEL_B, days_ago(-1))
    assert not lent(page, app.base_url, "PC-003"), "未来の貸出日は受け付けない"


@pytest.mark.stage1
def test_rule_b4_staff_cannot_borrow(app, page):
    app.seed({"accounts": [STAFF, EMP_A], "equipment": pcs(1)})
    login(page, app.base_url, STAFF["number"])
    page.goto(app.base_url)
    equipment_row(page, "PC-001").get_by_role("button", name="貸出").click()
    expect(page.locator("#id_borrower option", has_text="社員花子（000002）")).to_have_count(1)
    expect(page.locator("#id_borrower option", has_text="担当太郎")).to_have_count(0)


@pytest.mark.stage1
def test_rule_b5_equipment_number_ignores_case(app, page):
    app.seed({"accounts": [STAFF]})
    login(page, app.base_url, STAFF["number"])
    for number, name in [("pc-001", "ノートパソコン"), ("Pc-001", "モニター")]:
        page.goto(f"{app.base_url}/equipment/new/")
        page.fill("#id_equipment_number", number)
        page.fill("#id_name", name)
        save_button(page).click()
        page.wait_for_load_state()
    page.goto(app.base_url)
    expect(page.locator("tbody tr")).to_have_count(1)
    expect(equipment_row(page, "PC-001")).to_contain_text("ノートパソコン")


@pytest.mark.stage1
def test_rule_b6_overdue_after_14_days(app, page):
    app.seed({"accounts": [STAFF, EMP_A, EMP_B], "equipment": pcs(2)})
    login(page, app.base_url, STAFF["number"])
    try_lend(page, app.base_url, "PC-001", LABEL_A, days_ago(15))
    try_lend(page, app.base_url, "PC-002", LABEL_B, days_ago(14))
    assert "期限超過" in status_text(page, app.base_url, "PC-001"), "貸出日から 15 日で期限超過"
    text = status_text(page, app.base_url, "PC-002")
    assert "貸出中" in text and "期限超過" not in text, "14 日目までは貸出中"


@pytest.mark.stage1
def test_rule_b7_no_lending_to_overdue_borrower(app, page):
    app.seed({"accounts": [STAFF, EMP_A], "equipment": pcs(2)})
    login(page, app.base_url, STAFF["number"])
    try_lend(page, app.base_url, "PC-001", LABEL_A, days_ago(15))
    assert lent(page, app.base_url, "PC-001")
    try_lend(page, app.base_url, "PC-002", LABEL_A)
    assert not lent(page, app.base_url, "PC-002"), "期限を過ぎた備品を持つ社員には貸し出せない"
    page.goto(app.base_url)
    click_with_dialog(page, equipment_row(page, "PC-001").get_by_role("button", name="返却"), True)
    page.wait_for_load_state()
    try_lend(page, app.base_url, "PC-002", LABEL_A)
    assert lent(page, app.base_url, "PC-002"), "返却したあとは貸し出せる"


@pytest.mark.stage1
def test_rule_b8_no_delete_while_lent(app, page):
    app.seed({"accounts": [STAFF, EMP_A], "equipment": pcs(1)})
    login(page, app.base_url, STAFF["number"])
    try_lend(page, app.base_url, "PC-001", LABEL_A)
    page.goto(app.base_url)
    delete = equipment_row(page, "PC-001").get_by_role("button", name="削除")
    if delete.count() > 0:
        click_with_dialog(page, delete, True)
        page.wait_for_load_state()
    page.goto(app.base_url)
    expect(page.locator("tbody tr")).to_have_count(1)
    assert lent(page, app.base_url, "PC-001")
