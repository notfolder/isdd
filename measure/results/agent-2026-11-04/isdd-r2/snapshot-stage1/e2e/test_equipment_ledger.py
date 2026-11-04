"""E2E テスト（Playwright の Chromium で画面を操作する）。要件定義書のテスト用利用シナリオ 12 本に対応する。"""

import sys
import time
from pathlib import Path

from playwright.sync_api import expect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from equipment_ledger.core.db import initialize_schema, open_connection  # noqa: E402

MSG_REGISTERED = "登録しました。ログインしてください"
MSG_LOGIN_FAILED = "社員番号またはパスワードが違います"
MSG_DENY = "この操作は担当者だけが行えます"
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
        conn.execute("INSERT INTO equipment VALUES (?, ?)", (f"EQ-{i:04d}", f"備品 {i}"))
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
