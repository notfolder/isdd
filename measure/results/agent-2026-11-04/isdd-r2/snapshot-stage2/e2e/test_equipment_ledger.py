"""E2E テスト（Playwright の Chromium で画面を操作する）。要件定義書のテスト用利用シナリオに対応する。"""

import http.cookiejar
import sys
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from playwright.sync_api import expect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from equipment_ledger.core.db import initialize_schema, open_connection  # noqa: E402

MSG_REGISTERED = "登録しました。ログインしてください"
MSG_LOGIN_FAILED = "社員番号またはパスワードが違います"
MSG_DENY = "この操作は担当者だけが行えます"
MSG_ALREADY_LENT = "この備品は既に貸出中です"
MSG_ALREADY_RETURNED = "この備品は既に返却されています"
MSG_DELETE_LENT = "この備品は貸出中のため削除できません。先に返却を処理してください"
MSG_STALE_EDIT = "他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください"
JST = timezone(timedelta(hours=9))
PASSWORD = "12345678"


def register(page, base, number, name, password=PASSWORD):
    page.goto(base + "/accounts/register/")
    page.fill("#id_employee_number", number)
    page.fill("#id_name", name)
    page.fill("#id_password", password)
    page.get_by_role("button", name="登録", exact=True).click()


def login(page, base, number, password=PASSWORD):
    page.goto(base + "/login/")
    page.fill("#id_employee_number", number)
    page.fill("#id_password", password)
    page.get_by_role("button", name="ログイン", exact=True).click()


def logout(page):
    page.get_by_role("button", name="ログアウト", exact=True).click()


def save_equipment(page, base, number, name):
    page.goto(base + "/equipment/new/")
    page.fill("#id_equipment_number", number)
    page.fill("#id_name", name)
    page.get_by_role("button", name="保存", exact=True).click()


def make_staff_session(page, base):
    """担当者（最初の登録者）と社員（2 件目）を作り、担当者でログインした状態にする。"""
    register(page, base, "123456", "担当太郎")
    expect(page.locator(".message")).to_have_text(MSG_REGISTERED)
    register(page, base, "234567", "社員花子")
    login(page, base, "123456")
    expect(page.locator(".current-user")).to_have_text("担当太郎")


def test_register_first_account_as_staff(page, start_app):
    base = start_app()
    register(page, base, "123456", "担当太郎")
    expect(page.locator(".message")).to_have_text(MSG_REGISTERED)
    register(page, base, "234567", "社員花子")
    expect(page.locator(".message")).to_have_text(MSG_REGISTERED)

    login(page, base, "123456")
    expect(page.locator(".current-user")).to_have_text("担当太郎")
    expect(page.get_by_role("link", name="備品を登録")).to_be_visible()
    logout(page)

    login(page, base, "234567")
    expect(page.locator(".current-user")).to_have_text("社員花子")
    expect(page.get_by_role("link", name="備品を登録")).to_have_count(0)


def test_reject_account_input(page, start_app):
    base = start_app()
    register(page, base, "123456", "担当太郎")
    page.goto(base + "/accounts/register/")
    page.fill("#id_employee_number", "12345")
    page.fill("#id_name", "")
    page.fill("#id_password", "1234567")
    page.get_by_role("button", name="登録", exact=True).click()
    expect(page.locator(".field:has(#id_employee_number) .field-error")).to_have_text(
        "社員番号は 6 桁の数字で入力してください"
    )
    expect(page.locator(".field:has(#id_name) .field-error")).to_have_text("名前を入力してください")
    expect(page.locator(".field:has(#id_password) .field-error")).to_have_text(
        "パスワードは 8 文字以上で入力してください"
    )
    expect(page.locator("#id_employee_number")).to_have_value("12345")

    page.fill("#id_employee_number", "123456")
    page.fill("#id_name", "重複")
    page.fill("#id_password", PASSWORD)
    page.get_by_role("button", name="登録", exact=True).click()
    expect(page.locator(".field:has(#id_employee_number) .field-error")).to_have_text(
        "この社員番号は既に登録されています"
    )
    expect(page.locator("#id_name")).to_have_value("重複")


def test_login_and_logout(page, start_app):
    base = start_app()
    register(page, base, "123456", "担当太郎")
    login(page, base, "123456", password="wrong-pass")
    expect(page.locator(".error")).to_have_text(MSG_LOGIN_FAILED)
    login(page, base, "999999", password=PASSWORD)
    expect(page.locator(".error")).to_have_text(MSG_LOGIN_FAILED)

    login(page, base, "123456")
    expect(page.locator(".current-user")).to_have_text("担当太郎")
    logout(page)
    expect(page.locator(".current-user")).to_have_count(0)
    expect(page.get_by_role("link", name="ログイン")).to_be_visible()


def test_auto_logout_after_idle(page, start_app):
    base = start_app(idle_seconds=2)
    register(page, base, "123456", "担当太郎")
    login(page, base, "123456")
    expect(page.locator(".current-user")).to_have_text("担当太郎")
    time.sleep(3)
    page.goto(base + "/")
    expect(page.locator(".current-user")).to_have_count(0)
    expect(page.get_by_role("link", name="ログイン")).to_be_visible()


def test_register_equipment_as_staff(page, start_app):
    base = start_app()
    make_staff_session(page, base)
    save_equipment(page, base, "PC-0001", "ノートパソコン")
    row = page.locator('tbody tr[data-equipment-number="PC-0001"]')
    expect(row).to_contain_text("ノートパソコン")
    expect(row).to_contain_text("空き")


def test_reject_equipment_input(page, start_app):
    base = start_app()
    make_staff_session(page, base)
    save_equipment(page, base, "PC-0001", "ノートパソコン")

    save_equipment(page, base, "PC 0001", "n" * 51)
    expect(page.locator(".field:has(#id_equipment_number) .field-error")).to_have_text(
        "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください"
    )
    expect(page.locator(".field:has(#id_name) .field-error")).to_have_text(
        "備品名は 50 文字以内で入力してください"
    )
    expect(page.locator("#id_equipment_number")).to_have_value("PC 0001")

    save_equipment(page, base, "PC-0001", "別の名前")
    expect(page.locator(".field:has(#id_equipment_number) .field-error")).to_have_text(
        "この管理番号は既に使われています"
    )
    expect(page.locator("#id_name")).to_have_value("別の名前")


def test_update_equipment(page, start_app):
    base = start_app()
    make_staff_session(page, base)
    save_equipment(page, base, "PC-0001", "ノートパソコン")
    page.locator('tbody tr[data-equipment-number="PC-0001"]').get_by_role(
        "button", name="修正", exact=True
    ).click()
    page.fill("#id_name", "ノートパソコン（新）")
    page.get_by_role("button", name="保存", exact=True).click()
    row = page.locator('tbody tr[data-equipment-number="PC-0001"]')
    expect(row).to_contain_text("ノートパソコン（新）")
    expect(page.locator("tbody tr")).to_have_count(1)


def test_delete_equipment(page, start_app):
    base = start_app()
    make_staff_session(page, base)
    save_equipment(page, base, "PC-0001", "ノートパソコン")
    row_delete = page.locator('tbody tr[data-equipment-number="PC-0001"]').get_by_role(
        "button", name="削除", exact=True
    )

    page.once("dialog", lambda d: d.dismiss())
    row_delete.click()
    expect(page.locator('tbody tr[data-equipment-number="PC-0001"]')).to_have_count(1)

    page.once("dialog", lambda d: d.accept())
    row_delete.click()
    expect(page.locator('tbody tr[data-equipment-number="PC-0001"]')).to_have_count(0)
    expect(page.get_by_text("備品は登録されていません")).to_be_visible()


def test_view_status_without_login(page, start_app):
    base = start_app()
    make_staff_session(page, base)
    save_equipment(page, base, "PC-0002", "モニター")
    save_equipment(page, base, "PC-0001", "ノートパソコン")
    logout(page)
    page.context.clear_cookies()

    page.goto(base + "/")
    numbers = page.locator("tbody tr").evaluate_all("els => els.map(e => e.dataset.equipmentNumber)")
    assert numbers == ["PC-0001", "PC-0002"]
    expect(page.locator("tbody tr").first.locator("td").nth(2)).to_have_text("空き")
    expect(page.locator("tbody button")).to_have_count(0)
    expect(page.get_by_role("link", name="ログイン")).to_be_visible()
    expect(page.get_by_role("link", name="アカウント登録")).to_be_visible()


def test_view_empty_status(page, start_app):
    base = start_app()
    page.goto(base + "/")
    expect(page.get_by_text("備品は登録されていません")).to_be_visible()
    expect(page.locator("tbody tr")).to_have_count(0)


def test_deny_non_staff(page, start_app):
    base = start_app()
    make_staff_session(page, base)
    save_equipment(page, base, "PC-0001", "ノートパソコン")
    logout(page)

    # 社員でログインし、削除と登録画面の要求を直接送る
    login(page, base, "234567")
    expect(page.locator(".current-user")).to_have_text("社員花子")
    resp = page.request.post(base + "/equipment/PC-0001/delete/")
    assert MSG_DENY in resp.text()
    resp = page.request.get(base + "/equipment/new/")
    assert MSG_DENY in resp.text()
    page.goto(base + "/")
    expect(page.locator('tbody tr[data-equipment-number="PC-0001"]')).to_have_count(1)

    # 未ログインでも同じ要求は通らず、ログイン画面へ戻る
    logout(page)
    page.context.clear_cookies()
    resp = page.request.post(base + "/equipment/PC-0001/delete/")
    assert MSG_DENY in resp.text()
    assert "ログイン" in resp.text()
    page.goto(base + "/")
    expect(page.locator('tbody tr[data-equipment-number="PC-0001"]')).to_have_count(1)


def test_performance_within_limit(page, start_app, tmp_path):
    base = start_app()
    make_staff_session(page, base)
    logout(page)
    conn = open_connection(str(tmp_path / "data"))
    initialize_schema(conn)
    conn.execute("BEGIN IMMEDIATE")
    for i in range(300):
        conn.execute(
            "INSERT INTO equipment (equipment_number, name) VALUES (?, ?)", (f"EQ-{i:04d}", f"備品 {i}")
        )
    for i in range(50):
        conn.execute(
            "INSERT INTO account VALUES (?, ?, ?, 'member')", (f"8{i:05d}", f"社員{i}", "x")
        )
    conn.execute("COMMIT")
    conn.close()

    start = time.time()
    page.goto(base + "/")
    expect(page.locator("tbody tr")).to_have_count(300)
    elapsed = time.time() - start
    assert elapsed < 3, f"表示に {elapsed:.2f} 秒かかった"


def _today() -> str:
    return datetime.now(JST).date().isoformat()


def _lend_via_ui(page, base, number, borrower_label):
    page.locator('tbody tr[data-equipment-number="%s"]' % number).get_by_role(
        "button", name="貸出", exact=True
    ).click()
    page.select_option("#id_borrower", label=borrower_label)
    page.get_by_role("button", name="登録", exact=True).click()


def _member_opener(base, number, password=PASSWORD):
    """ログイン済みの HTTP の接続（Cookie を持つ opener）を返す。"""
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    data = urllib.parse.urlencode({"employee_number": number, "password": password}).encode()
    opener.open(base + "/login/", data=data).read()
    return opener


def _race(base, url, count, data_for=None):
    """count 個の接続から同時に url へ POST し、応答の本文の一覧を返す。"""
    openers = [_member_opener(base, "123456") for _ in range(count)]
    barrier = threading.Barrier(count)
    bodies = [None] * count

    def run(i):
        barrier.wait()
        data = urllib.parse.urlencode(data_for or {}).encode()
        bodies[i] = openers[i].open(base + url, data=data).read().decode("utf-8")

    threads = [threading.Thread(target=run, args=(i,)) for i in range(count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return bodies


def test_lend_equipment_as_staff(page, start_app):
    base = start_app()
    make_staff_session(page, base)
    save_equipment(page, base, "PC-0001", "ノートパソコン")
    _lend_via_ui(page, base, "PC-0001", "社員花子（234567）")
    row = page.locator('tbody tr[data-equipment-number="PC-0001"]')
    expect(row).to_contain_text("貸出中")
    expect(row).to_contain_text("社員花子")
    expect(row).to_contain_text(_today())


def test_reject_invalid_lend(page, start_app):
    base = start_app()
    make_staff_session(page, base)
    save_equipment(page, base, "PC-0001", "ノートパソコン")
    page.locator('tbody tr[data-equipment-number="PC-0001"]').get_by_role(
        "button", name="貸出", exact=True
    ).click()
    page.get_by_role("button", name="登録", exact=True).click()
    expect(page.locator(".field:has(#id_borrower) .field-error")).to_have_text("借りる社員を選んでください")

    page.select_option("#id_borrower", label="社員花子（234567）")
    tomorrow = (datetime.now(JST).date() + timedelta(days=1)).isoformat()
    page.fill("#id_lent_on", tomorrow)
    page.get_by_role("button", name="登録", exact=True).click()
    expect(page.locator(".field:has(#id_lent_on) .field-error")).to_have_text(
        "貸出日に未来の日付は入力できません"
    )

    page.fill("#id_lent_on", _today())
    page.get_by_role("button", name="登録", exact=True).click()
    expect(page.locator('tbody tr[data-equipment-number="PC-0001"]')).to_contain_text("貸出中")

    page.goto(base + "/equipment/PC-0001/lend/")
    page.select_option("#id_borrower", label="担当太郎（123456）")
    page.get_by_role("button", name="登録", exact=True).click()
    expect(page.locator(".message")).to_have_text(MSG_ALREADY_LENT)


def test_return_equipment_as_staff(page, start_app):
    base = start_app()
    make_staff_session(page, base)
    save_equipment(page, base, "PC-0001", "ノートパソコン")
    _lend_via_ui(page, base, "PC-0001", "社員花子（234567）")
    row_return = page.locator('tbody tr[data-equipment-number="PC-0001"]').get_by_role(
        "button", name="返却", exact=True
    )

    page.once("dialog", lambda d: d.dismiss())
    row_return.click()
    expect(page.locator('tbody tr[data-equipment-number="PC-0001"]')).to_contain_text("貸出中")

    page.once("dialog", lambda d: d.accept())
    row_return.click()
    row = page.locator('tbody tr[data-equipment-number="PC-0001"]')
    expect(row).to_contain_text("空き")
    expect(row).not_to_contain_text("社員花子")

    resp = page.request.post(base + "/equipment/PC-0001/return/")
    assert MSG_ALREADY_RETURNED in resp.text()


def test_deny_delete_while_lent(page, start_app):
    base = start_app()
    make_staff_session(page, base)
    save_equipment(page, base, "PC-0001", "ノートパソコン")
    _lend_via_ui(page, base, "PC-0001", "社員花子（234567）")
    page.once("dialog", lambda d: d.accept())
    page.locator('tbody tr[data-equipment-number="PC-0001"]').get_by_role(
        "button", name="削除", exact=True
    ).click()
    expect(page.locator(".message")).to_have_text(MSG_DELETE_LENT)
    expect(page.locator('tbody tr[data-equipment-number="PC-0001"]')).to_contain_text("貸出中")


def test_edit_keeps_lending(page, start_app):
    base = start_app()
    make_staff_session(page, base)
    save_equipment(page, base, "PC-0001", "ノートパソコン")
    _lend_via_ui(page, base, "PC-0001", "社員花子（234567）")
    page.locator('tbody tr[data-equipment-number="PC-0001"]').get_by_role(
        "button", name="修正", exact=True
    ).click()
    page.fill("#id_name", "ノートパソコン（新）")
    page.get_by_role("button", name="保存", exact=True).click()
    row = page.locator('tbody tr[data-equipment-number="PC-0001"]')
    expect(row).to_contain_text("ノートパソコン（新）")
    expect(row).to_contain_text("貸出中")
    expect(row).to_contain_text("社員花子")


def test_reject_stale_edit(page, start_app):
    base = start_app()
    make_staff_session(page, base)
    save_equipment(page, base, "PC-0001", "ノートパソコン")
    page.locator('tbody tr[data-equipment-number="PC-0001"]').get_by_role(
        "button", name="修正", exact=True
    ).click()

    # 別の画面（同じ担当者）で先に修正して保存する
    other = page.context.new_page()
    other.goto(base + "/equipment/PC-0001/edit/")
    other.fill("#id_name", "先の変更")
    other.get_by_role("button", name="保存", exact=True).click()
    expect(other.locator('tbody tr[data-equipment-number="PC-0001"]')).to_contain_text("先の変更")
    other.close()

    page.fill("#id_name", "後の変更")
    page.get_by_role("button", name="保存", exact=True).click()
    expect(page.locator(".error")).to_have_text(MSG_STALE_EDIT)
    page.goto(base + "/")
    expect(page.locator('tbody tr[data-equipment-number="PC-0001"]')).to_contain_text("先の変更")


def test_concurrent_lend_only_first_recorded(page, start_app):
    base = start_app()
    make_staff_session(page, base)
    save_equipment(page, base, "PC-0001", "ノートパソコン")
    bodies = _race(
        base,
        "/equipment/PC-0001/lend/",
        2,
        {"borrower": "234567", "lent_on": _today()},
    )
    assert sum(MSG_ALREADY_LENT in b for b in bodies) == 1
    page.goto(base + "/")
    row = page.locator('tbody tr[data-equipment-number="PC-0001"]')
    expect(row).to_contain_text("貸出中")
    expect(row).to_contain_text("社員花子")


def test_concurrent_return_only_first_processed(page, start_app):
    base = start_app()
    make_staff_session(page, base)
    save_equipment(page, base, "PC-0001", "ノートパソコン")
    _lend_via_ui(page, base, "PC-0001", "社員花子（234567）")
    bodies = _race(base, "/equipment/PC-0001/return/", 2)
    assert sum(MSG_ALREADY_RETURNED in b for b in bodies) == 1
    page.goto(base + "/")
    expect(page.locator('tbody tr[data-equipment-number="PC-0001"]')).to_contain_text("空き")


def test_deny_non_staff_lending(page, start_app):
    base = start_app()
    make_staff_session(page, base)
    save_equipment(page, base, "PC-0001", "ノートパソコン")
    _lend_via_ui(page, base, "PC-0001", "社員花子（234567）")
    logout(page)

    login(page, base, "234567")
    expect(page.locator(".current-user")).to_have_text("社員花子")
    resp = page.request.post(base + "/equipment/PC-0001/return/")
    assert MSG_DENY in resp.text()
    resp = page.request.get(base + "/equipment/PC-0001/lend/")
    assert MSG_DENY in resp.text()
    page.goto(base + "/")
    expect(page.locator('tbody tr[data-equipment-number="PC-0001"]')).to_contain_text("貸出中")

    logout(page)
    page.context.clear_cookies()
    resp = page.request.post(base + "/equipment/PC-0001/return/")
    assert MSG_DENY in resp.text()
    assert "ログイン" in resp.text()
    page.goto(base + "/")
    expect(page.locator('tbody tr[data-equipment-number="PC-0001"]')).to_contain_text("貸出中")
