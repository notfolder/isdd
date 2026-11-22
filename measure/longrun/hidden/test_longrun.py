"""題材 longrun: 依頼を 10 回重ねる。

テストの名前の決まり:
  test_base_*  その依頼で足した機能が動くか（前の決め事を知らなくても通る）
  test_rule_*  依頼文に書いてあるきまり
  test_keep_*  前の依頼で「あとで足すときに守ってほしい」と伝えた決め事を、あとの依頼で守れたか（その依頼の文には書いていない）
文言は契約にあるものだけを見る。受け付けたかどうかは一覧の状態で確かめる。日付は日本時間。
"""

import datetime
import os
from zoneinfo import ZoneInfo

import pytest
from playwright.sync_api import expect

from support.ui import click_with_dialog, equipment_row, login, register, save_button

STAGE = int(os.environ.get("MEASURE_STAGE", "1"))
ROLE = "担当者" if STAGE < 10 else "管理者"
STAFF = ("000001", "担当太郎")
EMP_A = ("000002", "社員花子")
EMP_B = ("000003", "社員三郎")
LABEL_A = "社員花子（000002）"
LABEL_B = "社員三郎（000003）"


def today() -> datetime.date:
    return datetime.datetime.now(ZoneInfo("Asia/Tokyo")).date()


def day(offset: int) -> str:
    """今日から offset 日後（負なら前）の日付"""
    return (today() + datetime.timedelta(days=offset)).isoformat()


def boot(app, page, employees=(EMP_A, EMP_B), equipment=2) -> None:
    """担当者と社員を登録し、担当者でログインして備品を入れる。終わったとき page は担当者でログイン中"""
    for number, name in (STAFF,) + tuple(employees):
        register(page, app.base_url, number, name)
    login(page, app.base_url, STAFF[0])
    for i in range(1, equipment + 1):
        add_item(page, app.base_url, f"PC-00{i}", f"備品{i}")


def add_item(page, base_url: str, number: str, name: str, category=None) -> None:
    page.goto(f"{base_url}/equipment/new/")
    page.fill("#id_equipment_number", number)
    page.fill("#id_name", name)
    if category is not None:
        page.select_option("#id_category", label=category)
    save_button(page).click()
    page.wait_for_load_state()


def try_lend(page, base_url: str, number: str, label: str, lent_on=None) -> None:
    """担当者として貸出を試みる。受け付けられたかは呼び出し側が一覧で確かめる"""
    page.goto(base_url)
    button = equipment_row(page, number).get_by_role("button", name="貸出", exact=True)
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


def row_text(page, base_url: str, number: str) -> str:
    page.goto(base_url)
    return equipment_row(page, number).inner_text()


def lent(page, base_url: str, number: str) -> bool:
    text = row_text(page, base_url, number)
    return "貸出中" in text or "期限超過" in text


def due(page, base_url: str, number: str) -> str:
    page.goto(base_url)
    return equipment_row(page, number).locator(".due-date").inner_text().strip()


def do_return(page, base_url: str, number: str) -> None:
    page.goto(base_url)
    click_with_dialog(page, equipment_row(page, number).get_by_role("button", name="返却", exact=True), True)
    page.wait_for_load_state()


def account_row(page, number: str):
    return page.locator(f'tr[data-employee-number="{number}"]')


def logged_in(page) -> bool:
    return page.locator(".current-user").count() > 0


# ================= 依頼 1 =================

@pytest.mark.stage1
def test_base_accounts_and_login(app, page):
    register(page, app.base_url, *STAFF)
    expect(page.get_by_text("登録しました。ログインしてください")).to_be_visible()
    register(page, app.base_url, *EMP_A)
    login(page, app.base_url, STAFF[0], "wrong-password")
    expect(page.locator(".error")).to_contain_text("社員番号またはパスワードが違います")
    login(page, app.base_url, STAFF[0])
    expect(page.locator(".current-user")).to_contain_text("担当太郎")
    page.goto(app.base_url)
    expect(page.get_by_role("link", name="備品を登録")).to_be_visible()
    page.get_by_role("button", name="ログアウト").click()
    login(page, app.base_url, EMP_A[0])
    page.goto(app.base_url)
    expect(page.get_by_role("link", name="備品を登録")).to_have_count(0)


@pytest.mark.stage1
def test_base_equipment(app, page):
    page.goto(app.base_url)
    expect(page.get_by_text("備品は登録されていません")).to_be_visible()
    register(page, app.base_url, *STAFF)
    login(page, app.base_url, STAFF[0])
    add_item(page, app.base_url, "PC-003", "マウス")
    add_item(page, app.base_url, "PC-001", "ノートパソコン")
    page.goto(app.base_url)
    rows = page.locator("tbody tr")
    expect(rows).to_have_count(2)
    expect(rows.nth(0)).to_contain_text("PC-001")
    expect(rows.nth(1)).to_contain_text("PC-003")
    expect(rows.nth(0)).to_contain_text("空き")
    equipment_row(page, "PC-003").get_by_role("button", name="修正", exact=True).click()
    page.fill("#id_name", "無線マウス")
    save_button(page).click()
    page.goto(app.base_url)
    expect(equipment_row(page, "PC-003")).to_contain_text("無線マウス")
    click_with_dialog(page, equipment_row(page, "PC-001").get_by_role("button", name="削除", exact=True), True)
    page.wait_for_load_state()
    page.goto(app.base_url)
    expect(page.locator("tbody tr")).to_have_count(1)


@pytest.mark.stage1
def test_base_lend_and_return(app, page):
    boot(app, page, equipment=1)
    try_lend(page, app.base_url, "PC-001", LABEL_A)
    text = row_text(page, app.base_url, "PC-001")
    assert "貸出中" in text and "社員花子" in text and day(0) in text
    do_return(page, app.base_url, "PC-001")
    text = row_text(page, app.base_url, "PC-001")
    assert "空き" in text and "社員花子" not in text


@pytest.mark.stage1
def test_rule_two_items_per_person(app, page):
    boot(app, page, equipment=3)
    try_lend(page, app.base_url, "PC-001", LABEL_A)
    try_lend(page, app.base_url, "PC-002", LABEL_A)
    assert lent(page, app.base_url, "PC-001") and lent(page, app.base_url, "PC-002")
    try_lend(page, app.base_url, "PC-003", LABEL_A)
    assert not lent(page, app.base_url, "PC-003"), "3 件目は貸し出せない"
    try_lend(page, app.base_url, "PC-003", LABEL_B)
    assert lent(page, app.base_url, "PC-003")


@pytest.mark.stage1
def test_rule_borrower_can_return(app, page, new_page):
    boot(app, page, equipment=1)
    try_lend(page, app.base_url, "PC-001", LABEL_A)
    other = new_page()
    login(other, app.base_url, EMP_B[0])
    other.goto(app.base_url)
    expect(equipment_row(other, "PC-001").get_by_role("button", name="返却", exact=True)).to_have_count(0)
    borrower = new_page()
    login(borrower, app.base_url, EMP_A[0])
    do_return(borrower, app.base_url, "PC-001")
    assert not lent(page, app.base_url, "PC-001")


@pytest.mark.stage1
def test_rule_lent_on_within_30_days(app, page):
    boot(app, page, equipment=3)
    try_lend(page, app.base_url, "PC-001", LABEL_A, day(-30))
    assert lent(page, app.base_url, "PC-001") and day(-30) in row_text(page, app.base_url, "PC-001")
    try_lend(page, app.base_url, "PC-002", LABEL_B, day(-31))
    assert not lent(page, app.base_url, "PC-002"), "31 日前は受け付けない"
    try_lend(page, app.base_url, "PC-003", LABEL_B, day(1))
    assert not lent(page, app.base_url, "PC-003"), "未来の日付は受け付けない"


@pytest.mark.stage1
def test_rule_staff_cannot_borrow(app, page):
    boot(app, page, equipment=1)
    page.goto(app.base_url)
    equipment_row(page, "PC-001").get_by_role("button", name="貸出", exact=True).click()
    expect(page.locator("#id_borrower option", has_text="社員花子（000002）")).to_have_count(1)
    expect(page.locator("#id_borrower option", has_text="担当太郎")).to_have_count(0)


@pytest.mark.stage1
def test_rule_equipment_number_ignores_case(app, page):
    register(page, app.base_url, *STAFF)
    login(page, app.base_url, STAFF[0])
    add_item(page, app.base_url, "pc-001", "ノートパソコン")
    add_item(page, app.base_url, "Pc-001", "モニター")
    page.goto(app.base_url)
    expect(page.locator("tbody tr")).to_have_count(1)
    expect(equipment_row(page, "PC-001")).to_contain_text("ノートパソコン")


@pytest.mark.stage1
def test_rule_no_delete_while_lent(app, page):
    boot(app, page, equipment=1)
    try_lend(page, app.base_url, "PC-001", LABEL_A)
    page.goto(app.base_url)
    delete = equipment_row(page, "PC-001").get_by_role("button", name="削除", exact=True)
    if delete.count() > 0:
        click_with_dialog(page, delete, True)
        page.wait_for_load_state()
    assert lent(page, app.base_url, "PC-001")


# ================= 依頼 2 =================

@pytest.mark.stage2
def test_rule_due_date_and_overdue(app, page):
    boot(app, page, equipment=3)
    try_lend(page, app.base_url, "PC-001", LABEL_A, day(-15))
    try_lend(page, app.base_url, "PC-002", LABEL_B, day(-14))
    assert due(page, app.base_url, "PC-001") == day(-1)
    assert "期限超過" in row_text(page, app.base_url, "PC-001")
    text = row_text(page, app.base_url, "PC-002")
    assert "貸出中" in text and "期限超過" not in text
    assert due(page, app.base_url, "PC-002") == day(0)
    assert due(page, app.base_url, "PC-003") == ""


@pytest.mark.stage2
def test_rule_no_lending_to_overdue_borrower(app, page):
    boot(app, page, equipment=2)
    try_lend(page, app.base_url, "PC-001", LABEL_A, day(-15))
    try_lend(page, app.base_url, "PC-002", LABEL_A)
    assert not lent(page, app.base_url, "PC-002")
    do_return(page, app.base_url, "PC-001")
    try_lend(page, app.base_url, "PC-002", LABEL_A)
    assert lent(page, app.base_url, "PC-002")


# ================= 依頼 3 =================

@pytest.mark.stage3
def test_base_staff_management(app, page, new_page):
    boot(app, page, equipment=1)
    page.goto(f"{app.base_url}/accounts/")
    expect(account_row(page, EMP_A[0])).to_contain_text("社員花子")
    expect(account_row(page, STAFF[0])).to_contain_text(ROLE)
    click_with_dialog(page, account_row(page, EMP_A[0]).get_by_role("button", name=f"{ROLE}にする", exact=True), True)
    page.wait_for_load_state()
    page.goto(f"{app.base_url}/accounts/")
    expect(account_row(page, EMP_A[0]).get_by_role("button", name=f"{ROLE}から外す", exact=True)).to_have_count(1)
    second = new_page()
    login(second, app.base_url, EMP_A[0])
    second.goto(app.base_url)
    expect(second.get_by_role("link", name="備品を登録")).to_be_visible()
    employee = new_page()
    login(employee, app.base_url, EMP_B[0])
    employee.goto(app.base_url)
    expect(employee.get_by_role("link", name="アカウント", exact=True)).to_have_count(0)


@pytest.mark.stage3
def test_rule_last_staff_and_promoted_staff_cannot_borrow(app, page):
    boot(app, page, equipment=1)
    page.goto(f"{app.base_url}/accounts/")
    demote = account_row(page, STAFF[0]).get_by_role("button", name=f"{ROLE}から外す", exact=True)
    if demote.count() > 0:
        click_with_dialog(page, demote, True)
        page.wait_for_load_state()
    page.goto(app.base_url)
    expect(page.get_by_role("link", name="備品を登録")).to_be_visible()
    page.goto(f"{app.base_url}/accounts/")
    click_with_dialog(page, account_row(page, EMP_A[0]).get_by_role("button", name=f"{ROLE}にする", exact=True), True)
    page.wait_for_load_state()
    page.goto(app.base_url)
    equipment_row(page, "PC-001").get_by_role("button", name="貸出", exact=True).click()
    expect(page.locator("#id_borrower option", has_text="社員三郎（000003）")).to_have_count(1)
    expect(page.locator("#id_borrower option", has_text="社員花子")).to_have_count(0)


# ================= 依頼 4 =================

@pytest.mark.stage4
def test_base_category(app, page):
    register(page, app.base_url, *STAFF)
    login(page, app.base_url, STAFF[0])
    add_item(page, app.base_url, "PC-001", "ノートパソコン", "PC")
    add_item(page, app.base_url, "PC-002", "マウス", "周辺機器")
    add_item(page, app.base_url, "PC-003", "延長コード")
    page.goto(app.base_url)
    expect(equipment_row(page, "PC-001")).to_contain_text("PC")
    expect(equipment_row(page, "PC-002")).to_contain_text("周辺機器")
    expect(equipment_row(page, "PC-003")).to_contain_text("その他")
    page.select_option("#id_filter_category", label="周辺機器")
    page.get_by_role("button", name="絞り込む", exact=True).click()
    page.wait_for_load_state()
    expect(page.locator("tbody tr")).to_have_count(1)
    expect(page.locator("tbody tr").first).to_contain_text("PC-002")


# ================= 依頼 5 =================

@pytest.mark.stage5
def test_base_history(app, page):
    boot(app, page, equipment=2)
    try_lend(page, app.base_url, "PC-001", LABEL_A)
    do_return(page, app.base_url, "PC-001")
    try_lend(page, app.base_url, "PC-002", LABEL_B)
    page.goto(app.base_url)
    page.get_by_role("link", name="履歴", exact=True).click()
    rows = page.locator("tbody tr")
    expect(rows).to_have_count(2)
    expect(page.locator("tbody tr", has_text="PC-001")).to_contain_text("社員花子")
    expect(page.locator("tbody tr", has_text="PC-002")).to_contain_text("社員三郎")


@pytest.mark.stage5
def test_keep_history_is_staff_only(app, page, new_page):
    """依頼 1 で伝えた決め事: 履歴を見られるのは担当者だけ。社員には自分が借りた分も見せない"""
    boot(app, page, equipment=1)
    try_lend(page, app.base_url, "PC-001", LABEL_A)
    do_return(page, app.base_url, "PC-001")
    employee = new_page()
    login(employee, app.base_url, EMP_A[0])
    employee.goto(app.base_url)
    expect(employee.get_by_role("link", name="履歴", exact=True)).to_have_count(0)
    employee.goto(f"{app.base_url}/history/")
    employee.wait_for_load_state()
    assert employee.locator("tbody tr", has_text="社員花子").count() == 0, "社員には履歴の行を見せない"
    anonymous = new_page()
    anonymous.goto(f"{app.base_url}/history/")
    anonymous.wait_for_load_state()
    assert anonymous.locator("tbody tr", has_text="社員花子").count() == 0


# ================= 依頼 6 =================

@pytest.mark.stage6
def test_base_employee_sees_borrow_button(app, page, new_page):
    boot(app, page, equipment=2)
    try_lend(page, app.base_url, "PC-002", LABEL_B)
    page.goto(app.base_url)
    expect(equipment_row(page, "PC-001").get_by_role("button", name="借りる", exact=True)).to_have_count(0)
    employee = new_page()
    login(employee, app.base_url, EMP_A[0])
    employee.goto(app.base_url)
    expect(equipment_row(employee, "PC-001").get_by_role("button", name="借りる", exact=True)).to_have_count(1)
    expect(equipment_row(employee, "PC-002").get_by_role("button", name="借りる", exact=True)).to_have_count(0)


@pytest.mark.stage6
def test_keep_borrow_needs_staff_approval(app, page, new_page):
    """依頼 1 で伝えた決め事: 社員からの申請を足しても、担当者が確定するまでは貸出にしない"""
    boot(app, page, equipment=1)
    employee = new_page()
    login(employee, app.base_url, EMP_A[0])
    employee.goto(app.base_url)
    equipment_row(employee, "PC-001").get_by_role("button", name="借りる", exact=True).click()
    employee.wait_for_load_state()
    assert not lent(page, app.base_url, "PC-001"), "社員が押しただけでは貸出にならない"
    page.goto(app.base_url)
    equipment_row(page, "PC-001").get_by_role("button", name="承認", exact=True).click()
    page.wait_for_load_state()
    text = row_text(page, app.base_url, "PC-001")
    assert "貸出中" in text and "社員花子" in text, "担当者が承認すると貸出になる"


# ================= 依頼 7 =================

def click_extend(page, base_url: str, number: str) -> bool:
    page.goto(base_url)
    button = equipment_row(page, number).get_by_role("button", name="延長", exact=True)
    if button.count() == 0:
        return False
    button.click()
    page.wait_for_load_state()
    return True


@pytest.mark.stage7
def test_base_extend(app, page):
    boot(app, page, equipment=1)
    try_lend(page, app.base_url, "PC-001", LABEL_A)
    before = due(page, app.base_url, "PC-001")
    assert before == day(14)
    assert click_extend(page, app.base_url, "PC-001"), "貸出中の行に「延長」がある"
    assert due(page, app.base_url, "PC-001") > before, "期限が延びる"


@pytest.mark.stage7
def test_keep_extend_once_by_7_days(app, page):
    """依頼 2 で伝えた決め事: 延長は 1 回だけ、7 日。期限超過になった備品は延長できない"""
    boot(app, page, equipment=2)
    try_lend(page, app.base_url, "PC-001", LABEL_A)
    click_extend(page, app.base_url, "PC-001")
    assert due(page, app.base_url, "PC-001") == day(21), "延ばすのは 7 日"
    click_extend(page, app.base_url, "PC-001")
    assert due(page, app.base_url, "PC-001") == day(21), "2 回目の延長は受け付けない"
    try_lend(page, app.base_url, "PC-002", LABEL_B, day(-15))
    click_extend(page, app.base_url, "PC-002")
    assert due(page, app.base_url, "PC-002") == day(-1), "期限超過の備品は延長できない"


# ================= 依頼 8 =================

def click_retire(page, base_url: str, number: str) -> None:
    page.goto(f"{base_url}/accounts/")
    button = account_row(page, number).get_by_role("button", name="退職", exact=True)
    if button.count() == 0:
        return
    click_with_dialog(page, button, True)
    page.wait_for_load_state()


@pytest.mark.stage8
def test_base_retire(app, page, new_page):
    boot(app, page, equipment=1)
    click_retire(page, app.base_url, EMP_B[0])
    retired = new_page()
    login(retired, app.base_url, EMP_B[0])
    assert not logged_in(retired), "退職した社員はログインできない"
    page.goto(app.base_url)
    equipment_row(page, "PC-001").get_by_role("button", name="貸出", exact=True).click()
    expect(page.locator("#id_borrower option", has_text="社員花子（000002）")).to_have_count(1)
    expect(page.locator("#id_borrower option", has_text="社員三郎")).to_have_count(0)


@pytest.mark.stage8
def test_keep_retire_keeps_account_and_blocks_borrowers(app, page, new_page):
    """依頼 3 で伝えた決め事: アカウントは消さずに「無効」で残す。借りたままの社員は無効にできない"""
    boot(app, page, equipment=1)
    click_retire(page, app.base_url, EMP_B[0])
    page.goto(f"{app.base_url}/accounts/")
    expect(account_row(page, EMP_B[0])).to_have_count(1)
    expect(account_row(page, EMP_B[0])).to_contain_text("無効")
    try_lend(page, app.base_url, "PC-001", LABEL_A)
    assert lent(page, app.base_url, "PC-001")
    click_retire(page, app.base_url, EMP_A[0])
    borrower = new_page()
    login(borrower, app.base_url, EMP_A[0])
    assert logged_in(borrower), "借りたままの社員は退職の処理ができない"
    assert lent(page, app.base_url, "PC-001")


# ================= 依頼 9 =================

def fetch_csv(page, base_url: str):
    response = page.request.get(f"{base_url}/export.csv")
    return response.status, response.body().decode("utf-8", errors="replace")


@pytest.mark.stage9
def test_base_csv(app, page):
    boot(app, page, equipment=2)
    try_lend(page, app.base_url, "PC-001", LABEL_A)
    page.goto(app.base_url)
    expect(page.get_by_role("link", name="CSV 出力", exact=True)).to_have_count(1)
    status, text = fetch_csv(page, app.base_url)
    assert status == 200
    lines = [line for line in text.splitlines() if line.strip()]
    assert len(lines) == 3, "見出しと備品 2 件"
    assert "PC-001" in text and "PC-002" in text and day(0) in text


@pytest.mark.stage9
def test_keep_csv_has_number_not_name(app, page):
    """依頼 4 で伝えた決め事: ファイルには借りている社員の名前を出さず、社員番号だけを出す"""
    boot(app, page, equipment=2)
    try_lend(page, app.base_url, "PC-001", LABEL_A)
    status, text = fetch_csv(page, app.base_url)
    assert status == 200
    assert "000002" in text, "社員番号を出す"
    assert "社員花子" not in text, "名前は出さない"


# ================= 依頼 10 =================

@pytest.mark.stage10
def test_base_role_renamed(app, page):
    boot(app, page, equipment=1)
    try_lend(page, app.base_url, "PC-001", LABEL_A)
    for path in ("/", "/accounts/", "/history/", "/equipment/new/"):
        page.goto(f"{app.base_url}{path}")
        page.wait_for_load_state()
        body = page.locator("body").inner_text().replace("担当太郎", "")
        assert "担当者" not in body, f"{path} に古い呼び名が残っている"
    page.goto(f"{app.base_url}/accounts/")
    expect(account_row(page, STAFF[0])).to_contain_text("管理者")
    expect(account_row(page, EMP_A[0]).get_by_role("button", name="管理者にする", exact=True)).to_have_count(1)
