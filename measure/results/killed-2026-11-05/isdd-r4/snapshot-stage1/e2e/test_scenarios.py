"""E2E テスト（要件定義書 第 7 章のテスト用利用シナリオを 1 関数 1 シナリオで確かめる）。"""

import re
import sqlite3
import time

from playwright.sync_api import expect

from e2e.support import save_equipment, login, logout, register


def test_register_first_account(make_server, page):
    """最初の登録は担当者になる。"""
    base = make_server().url
    register(page, base, "000001", "山田太郎")
    expect(page.locator(".message")).to_have_text("登録しました。ログインしてください")
    login(page, base, "000001")
    expect(page.locator(".current-user")).to_have_text("山田太郎")
    expect(page.get_by_role("link", name="備品を登録", exact=True)).to_be_visible()


def test_register_validation(make_server, page):
    """登録の入力チェックと、入力値の保持。"""
    base = make_server().url
    register(page, base, "000001", "山田太郎")
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

    page.fill("#id_employee_number", "000001")
    page.fill("#id_name", "あ" * 31)
    page.fill("#id_password", "password1")
    page.get_by_role("button", name="登録", exact=True).click()
    expect(page.locator(".field:has(#id_name) .field-error")).to_have_text("名前は 30 文字以内で入力してください")

    page.fill("#id_name", "山田太郎")
    page.get_by_role("button", name="登録", exact=True).click()
    expect(page.locator(".field:has(#id_employee_number) .field-error")).to_have_text(
        "この社員番号は既に登録されています"
    )


def test_register_second_account(make_server, page):
    """2 件目以降は社員になり、担当者の操作はできない。"""
    base = make_server().url
    register(page, base, "000001", "山田太郎")
    register(page, base, "000002", "佐藤花子", "password2")
    login(page, base, "000002", "password2")
    expect(page.locator(".current-user")).to_have_text("佐藤花子")
    expect(page.get_by_role("link", name="備品を登録", exact=True)).to_have_count(0)
    page.goto(base + "/equipment/new/")
    expect(page.locator(".message")).to_have_text("この操作は担当者だけが行えます")


def test_login_and_failure(make_server, page):
    """ログインの成功と、失敗時の文言（どちらが違うかは示さない）。"""
    base = make_server().url
    register(page, base, "000001", "山田太郎")
    login(page, base, "000001", "wrong-pass")
    expect(page.locator(".error")).to_have_text("社員番号またはパスワードが違います")
    login(page, base, "999999", "password1")
    expect(page.locator(".error")).to_have_text("社員番号またはパスワードが違います")
    login(page, base, "000001", "password1")
    expect(page.locator(".current-user")).to_have_text("山田太郎")


def test_logout(make_server, page):
    """ログアウトすると名前が消え、ログインのリンクが出る。"""
    base = make_server().url
    register(page, base, "000001", "山田太郎")
    login(page, base, "000001")
    logout(page)
    expect(page.locator(".current-user")).to_have_count(0)
    expect(page.get_by_role("link", name="ログイン", exact=True)).to_be_visible()


def test_idle_timeout(make_server, page):
    """操作しないまま期限を過ぎると自動でログアウトする（テストでは 2 秒）。"""
    base = make_server(idle_timeout=2).url
    register(page, base, "000001", "山田太郎")
    login(page, base, "000001")
    expect(page.locator(".current-user")).to_have_text("山田太郎")
    time.sleep(3)
    page.goto(base + "/")
    expect(page.locator(".current-user")).to_have_count(0)
    page.goto(base + "/equipment/new/")
    expect(page).to_have_url(re.compile(r".*/login/$"))


def test_create_equipment(make_server, page):
    """担当者が備品を登録し、一覧に管理番号の昇順で出る。"""
    base = make_server().url
    register(page, base, "000001", "山田太郎")
    login(page, base, "000001")
    save_equipment(page, base, "EQ-0002", "椅子")
    expect(page.locator(".message")).to_have_text("備品を登録しました")
    save_equipment(page, base, "EQ-0001", "ノートパソコン")
    row = page.locator("tbody tr[data-equipment-number='EQ-0001']")
    expect(row).to_contain_text("ノートパソコン")
    expect(row).to_contain_text("空き")
    expect(page.locator("tbody tr").first).to_have_attribute("data-equipment-number", "EQ-0001")


def test_create_equipment_validation(make_server, page):
    """管理番号と備品名の検査、重複、入力値の保持。"""
    base = make_server().url
    register(page, base, "000001", "山田太郎")
    login(page, base, "000001")
    save_equipment(page, base, "EQ-0001", "ノートパソコン")

    page.goto(base + "/equipment/new/")
    page.fill("#id_equipment_number", "A" * 21)
    page.fill("#id_name", "x" * 51)
    page.get_by_role("button", name="保存", exact=True).click()
    expect(page.locator(".field:has(#id_equipment_number) .field-error")).to_have_text(
        "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください"
    )
    expect(page.locator(".field:has(#id_name) .field-error")).to_have_text("備品名は 50 文字以内で入力してください")
    expect(page.locator("#id_equipment_number")).to_have_value("A" * 21)

    page.fill("#id_equipment_number", "EQ_001")
    page.fill("#id_name", "机")
    page.get_by_role("button", name="保存", exact=True).click()
    expect(page.locator(".field:has(#id_equipment_number) .field-error")).to_have_text(
        "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください"
    )

    page.fill("#id_equipment_number", "EQ-0001")
    page.get_by_role("button", name="保存", exact=True).click()
    expect(page.locator(".field:has(#id_equipment_number) .field-error")).to_have_text(
        "この管理番号は既に使われています"
    )


def test_update_equipment(make_server, page):
    """担当者が備品名を修正し、一覧に新しい名前が出る。"""
    base = make_server().url
    register(page, base, "000001", "山田太郎")
    login(page, base, "000001")
    save_equipment(page, base, "EQ-0001", "旧名")
    page.locator("tr[data-equipment-number='EQ-0001']").get_by_role("button", name="修正", exact=True).click()
    expect(page.locator("#id_equipment_number")).to_have_value("EQ-0001")
    page.fill("#id_name", "新名")
    page.get_by_role("button", name="保存", exact=True).click()
    expect(page.locator(".message")).to_have_text("備品を修正しました")
    expect(page.locator("tr[data-equipment-number='EQ-0001']")).to_contain_text("新名")


def test_delete_equipment(make_server, page):
    """確認ダイアログで「キャンセル」なら残り、「はい」なら消える。"""
    base = make_server().url
    register(page, base, "000001", "山田太郎")
    login(page, base, "000001")
    save_equipment(page, base, "EQ-0001", "ノートパソコン")
    row_delete = page.locator("tr[data-equipment-number='EQ-0001']").get_by_role("button", name="削除", exact=True)

    page.once("dialog", lambda dialog: dialog.dismiss())
    row_delete.click()
    expect(page.locator("tr[data-equipment-number='EQ-0001']")).to_have_count(1)

    page.once("dialog", lambda dialog: dialog.accept())
    row_delete.click()
    expect(page.locator("tr[data-equipment-number='EQ-0001']")).to_have_count(0)
    expect(page.locator(".message")).to_have_text("備品を削除しました")


def test_loan_status_anonymous(make_server, page):
    """未ログインでも一覧が見える。0 件の表示と、ボタンが無いこと。"""
    base = make_server().url
    page.goto(base + "/")
    expect(page.locator("p", has_text="備品は登録されていません")).to_be_visible()

    register(page, base, "000001", "山田太郎")
    login(page, base, "000001")
    save_equipment(page, base, "EQ-0001", "ノートパソコン")
    logout(page)

    page.goto(base + "/")
    row = page.locator("tbody tr[data-equipment-number='EQ-0001']")
    expect(row).to_contain_text("空き")
    expect(page.get_by_role("button", name="修正", exact=True)).to_have_count(0)
    expect(page.get_by_role("button", name="削除", exact=True)).to_have_count(0)
    expect(page.get_by_role("link", name="ログイン", exact=True)).to_be_visible()
    expect(page.get_by_role("link", name="アカウント登録", exact=True)).to_be_visible()


def test_role_control(make_server, page):
    """社員にはボタンが無く、操作の要求は拒否される。未ログインはログイン画面へ。"""
    base = make_server().url
    register(page, base, "000001", "山田太郎")
    login(page, base, "000001")
    save_equipment(page, base, "EQ-0001", "ノートパソコン")
    logout(page)
    register(page, base, "000002", "佐藤花子", "password2")
    login(page, base, "000002", "password2")

    page.goto(base + "/")
    expect(page.get_by_role("button", name="修正", exact=True)).to_have_count(0)
    expect(page.get_by_role("button", name="削除", exact=True)).to_have_count(0)
    expect(page.get_by_role("link", name="備品を登録", exact=True)).to_have_count(0)

    # 社員が削除の要求を直接送っても、備品は消えず、一覧に戻る
    response = page.request.post(base + "/equipment/EQ-0001/delete/", max_redirects=0)
    assert response.status == 302
    page.goto(base + "/")
    expect(page.locator("tr[data-equipment-number='EQ-0001']")).to_have_count(1)

    page.goto(base + "/equipment/new/")
    expect(page).to_have_url(re.compile(r".*/$"))
    expect(page.locator(".message")).to_have_text("この操作は担当者だけが行えます")

    logout(page)
    page.goto(base + "/equipment/new/")
    expect(page).to_have_url(re.compile(r".*/login/$"))


def test_loan_status_performance(make_server, page):
    """備品 500 件のとき、3 秒以内に一覧が表示される。"""
    server = make_server()
    base = server.url
    with sqlite3.connect(server.app.config["DB_PATH"]) as conn:
        conn.executemany(
            "INSERT INTO equipment (equipment_number, name) VALUES (?, ?)",
            [(f"EQ-{i:04d}", f"備品 {i}") for i in range(1, 501)],
        )
    started = time.perf_counter()
    page.goto(base + "/")
    page.wait_for_selector("tbody tr")
    elapsed = time.perf_counter() - started
    assert len(page.locator("tbody tr").all()) == 500
    assert elapsed < 3.0, f"表示までに {elapsed:.2f} 秒かかりました"
