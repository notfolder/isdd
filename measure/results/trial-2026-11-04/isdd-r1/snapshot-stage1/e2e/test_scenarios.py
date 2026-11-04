"""利用シナリオに対応する E2E テスト。各テスト関数が 1 つの利用シナリオを確かめる。"""

import time
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen

from playwright.sync_api import expect

from werkzeug.security import generate_password_hash

from app import db

from .conftest import run_server
from .helpers import add_equipment, login, logout, register

FIELD_ERROR = ".field-error"


def test_register_first_manager(new_page, server):
    page = new_page()
    register(page, server, "100001", "山田 太郎", "password1")
    expect(page.locator(".message")).to_have_text("登録しました。ログインしてください")
    register(page, server, "100002", "佐藤 花子", "password2")
    login(page, server, "100001", "password1")
    page.goto(server + "/accounts/")
    expect(page.locator('tbody tr[data-employee-number="100001"] td').nth(2)).to_have_text("担当者")
    expect(page.locator('tbody tr[data-employee-number="100002"] td').nth(2)).to_have_text("社員")


def test_register_account_validation(new_page, server):
    page = new_page()
    page.goto(server + "/accounts/register/")
    page.fill("#id_employee_number", "12345")
    page.fill("#id_name", "")
    page.fill("#id_password", "short")
    page.get_by_role("button", name="登録").click()
    expect(page.locator(".field:has(#id_employee_number) " + FIELD_ERROR)).to_have_text("社員番号は 6 桁の数字で入力してください")
    expect(page.locator(".field:has(#id_name) " + FIELD_ERROR)).to_have_text("名前を入力してください")
    expect(page.locator(".field:has(#id_password) " + FIELD_ERROR)).to_have_text("パスワードは 8 文字以上で入力してください")
    expect(page.locator("#id_employee_number")).to_have_value("12345")

    page.fill("#id_employee_number", "100001")
    page.fill("#id_name", "a" * 31)
    page.fill("#id_password", "password1")
    page.get_by_role("button", name="登録").click()
    expect(page.locator(".field:has(#id_name) " + FIELD_ERROR)).to_have_text("名前は 30 文字以内で入力してください")
    expect(page.locator("#id_name")).to_have_value("a" * 31)

    page.fill("#id_name", "山田")
    page.fill("#id_password", "password1")
    page.get_by_role("button", name="登録").click()
    expect(page).to_have_url(server + "/login/")
    register(page, server, "100001", "別人", "password1")
    expect(page.locator(".field:has(#id_employee_number) " + FIELD_ERROR)).to_have_text("この社員番号は既に登録されています")


def test_login_logout(new_page, server):
    page = new_page()
    register(page, server, "100001", "山田 太郎", "password1")
    login(page, server, "100001", "wrong-password")
    expect(page.locator(".error")).to_have_text("社員番号またはパスワードが違います")
    login(page, server, "999999", "password1")
    expect(page.locator(".error")).to_have_text("社員番号またはパスワードが違います")
    login(page, server, "100001", "password1")
    expect(page.locator(".current-user")).to_have_text("山田 太郎")
    logout(page)
    expect(page.locator(".current-user")).to_have_count(0)
    page.goto(server + "/")
    expect(page.get_by_role("link", name="ログイン")).to_be_visible()


def test_idle_logout(new_page, data_dir):
    with run_server(data_dir, idle_timeout=3) as base:
        page = new_page()
        register(page, base, "100001", "山田 太郎", "password1")
        login(page, base, "100001", "password1")
        expect(page.locator(".current-user")).to_have_text("山田 太郎")
        time.sleep(4.5)
        page.goto(base + "/equipment/new/")
        expect(page).to_have_url(base + "/login/")


def test_role_check(new_page, server):
    page = new_page()
    register(page, server, "100001", "山田 太郎", "password1")
    register(page, server, "100002", "佐藤 花子", "password2")
    page.goto(server + "/")
    expect(page.get_by_role("button", name="修正")).to_have_count(0)
    expect(page.get_by_role("link", name="備品の登録")).to_have_count(0)
    expect(page.get_by_role("link", name="アカウントの一覧")).to_have_count(0)
    response = page.request.post(server + "/equipment/new/", form={"equipment_number": "EQ-9", "name": "x"})
    assert "/login/" in response.url
    login(page, server, "100002", "password2")
    page.goto(server + "/")
    expect(page.get_by_role("button", name="削除")).to_have_count(0)
    page.goto(server + "/accounts/")
    expect(page.locator(".message")).to_have_text("この操作は担当者だけが行えます")
    response = page.request.post(server + "/equipment/new/", form={"equipment_number": "EQ-9", "name": "x"})
    assert "この操作は担当者だけが行えます" in response.text()


def test_register_equipment(new_page, server):
    page = new_page()
    register(page, server, "100001", "山田 太郎", "password1")
    login(page, server, "100001", "password1")
    add_equipment(page, server, "EQ-0001", "ノートPC")
    expect(page.locator('tbody tr[data-equipment-number="EQ-0001"]')).to_contain_text("空き")
    page.goto(server + "/equipment/new/")
    page.fill("#id_equipment_number", "備品1")
    page.fill("#id_name", "b" * 51)
    page.get_by_role("button", name="保存").click()
    expect(page.locator(".field:has(#id_equipment_number) " + FIELD_ERROR)).to_have_text("管理番号は半角の英数字とハイフンで 20 文字以内で入力してください")
    expect(page.locator(".field:has(#id_name) " + FIELD_ERROR)).to_have_text("備品名は 50 文字以内で入力してください")
    expect(page.locator("#id_name")).to_have_value("b" * 51)
    page.fill("#id_equipment_number", "EQ-0001")
    page.fill("#id_name", "別の備品")
    page.get_by_role("button", name="保存").click()
    expect(page.locator(".field:has(#id_equipment_number) " + FIELD_ERROR)).to_have_text("この管理番号は既に使われています")


def test_edit_equipment(new_page, server):
    page_a = new_page()
    register(page_a, server, "100001", "山田 太郎", "password1")
    register(page_a, server, "100002", "佐藤 花子", "password2")
    login(page_a, server, "100001", "password1")
    add_equipment(page_a, server, "EQ-1", "椅子")
    page_a.goto(server + "/accounts/")
    page_a.locator('tbody tr[data-employee-number="100002"]').get_by_role("button", name="担当者にする").click()
    page_b = new_page()
    login(page_b, server, "100002", "password2")
    page_a.goto(server + "/equipment/EQ-1/edit/")
    page_b.goto(server + "/equipment/EQ-1/edit/")
    page_b.fill("#id_name", "椅子B")
    page_b.get_by_role("button", name="保存").click()
    expect(page_b.locator(".message")).to_have_text("備品を更新しました")
    page_a.fill("#id_name", "椅子A")
    page_a.get_by_role("button", name="保存").click()
    expect(page_a.locator(".error")).to_have_text("他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください")
    expect(page_a.locator('tbody tr[data-equipment-number="EQ-1"]')).to_contain_text("椅子B")


def test_delete_equipment(new_page, server):
    page = new_page()
    register(page, server, "100001", "山田 太郎", "password1")
    register(page, server, "100002", "佐藤 花子", "password2")
    login(page, server, "100001", "password1")
    add_equipment(page, server, "EQ-1", "椅子")
    add_equipment(page, server, "EQ-2", "机")
    page.goto(server + "/equipment/EQ-1/lend/")
    page.locator("#id_borrower").select_option(label="佐藤 花子（100002）")
    page.get_by_role("button", name="登録").click()
    page.goto(server + "/")
    page.locator('tbody tr[data-equipment-number="EQ-1"]').get_by_role("button", name="削除").click()
    expect(page.locator(".message")).to_have_text("この備品は貸出中のため削除できません。先に返却を処理してください")
    expect(page.locator('tbody tr[data-equipment-number="EQ-1"]')).to_have_count(1)
    page.locator('tbody tr[data-equipment-number="EQ-2"]').get_by_role("button", name="削除").click()
    expect(page.locator('tbody tr[data-equipment-number="EQ-2"]')).to_have_count(0)
    expect(page.locator(".message")).to_have_text("備品を削除しました")


def test_lend_return(new_page, server):
    page = new_page()
    register(page, server, "100001", "山田 太郎", "password1")
    register(page, server, "100002", "佐藤 花子", "password2")
    login(page, server, "100001", "password1")
    add_equipment(page, server, "EQ-1", "椅子")
    page.goto(server + "/equipment/EQ-1/lend/")
    stale = page.context.new_page()
    stale.on("dialog", lambda dialog: dialog.accept())
    stale.goto(server + "/equipment/EQ-1/lend/")
    page.get_by_role("button", name="登録").click()
    expect(page.locator(".field:has(#id_borrower) " + FIELD_ERROR)).to_have_text("借りる社員を選んでください")
    page.locator("#id_borrower").select_option(label="佐藤 花子（100002）")
    page.fill("#id_lent_on", "2099-01-01")
    page.get_by_role("button", name="登録").click()
    expect(page.locator(".field:has(#id_lent_on) " + FIELD_ERROR)).to_have_text("貸出日に未来の日付は入力できません")
    expect(page.locator(".lending-equipment")).to_have_text("備品: EQ-1 椅子")
    page.fill("#id_lent_on", time.strftime("%Y-%m-%d"))
    page.get_by_role("button", name="登録").click()
    row = page.locator('tbody tr[data-equipment-number="EQ-1"]')
    expect(row).to_contain_text("貸出中")
    expect(row).to_contain_text("佐藤 花子")
    stale.locator("#id_borrower").select_option(label="佐藤 花子（100002）")
    stale.get_by_role("button", name="登録").click()
    expect(stale.locator(".message")).to_have_text("この備品は既に貸出中です")
    row.get_by_role("button", name="返却").click()
    expect(page.locator('tbody tr[data-equipment-number="EQ-1"]')).to_contain_text("空き")
    response = page.request.post(server + "/equipment/EQ-1/return/", form={"version": "1"})
    assert "この備品は既に返却されています" in response.text()


def test_view_lending_status(new_page, server):
    page = new_page()
    page.goto(server + "/")
    expect(page.locator("p", has_text="備品は登録されていません")).to_be_visible()
    register(page, server, "100001", "山田 太郎", "password1")
    register(page, server, "100002", "佐藤 花子", "password2")
    login(page, server, "100001", "password1")
    add_equipment(page, server, "EQ-0003", "C")
    add_equipment(page, server, "EQ-0001", "A")
    add_equipment(page, server, "EQ-0002", "B")
    page.goto(server + "/equipment/EQ-0002/lend/")
    page.locator("#id_borrower").select_option(label="佐藤 花子（100002）")
    page.get_by_role("button", name="登録").click()
    logout(page)
    guest = new_page()
    guest.goto(server + "/")
    numbers = guest.locator("tbody tr").evaluate_all("rows => rows.map(r => r.dataset.equipmentNumber)")
    assert numbers == ["EQ-0001", "EQ-0002", "EQ-0003"]
    expect(guest.locator('tbody tr[data-equipment-number="EQ-0002"]')).to_contain_text("貸出中")
    expect(guest.locator('tbody tr[data-equipment-number="EQ-0002"]')).to_contain_text("佐藤 花子")
    expect(guest.locator('tbody tr[data-equipment-number="EQ-0001"]')).to_contain_text("空き")


def test_account_list_manage(new_page, server):
    page = new_page()
    register(page, server, "100001", "山田 太郎", "password1")
    register(page, server, "100002", "佐藤 花子", "password2")
    login(page, server, "100001", "password1")
    page.goto(server + "/accounts/")
    row2 = page.locator('tbody tr[data-employee-number="100002"]')
    row1 = page.locator('tbody tr[data-employee-number="100001"]')
    row2.get_by_role("button", name="担当者にする").click()
    expect(row2.locator("td").nth(2)).to_have_text("担当者")
    row2.get_by_role("button", name="担当者から外す").click()
    expect(row2.locator("td").nth(2)).to_have_text("社員")
    row1.get_by_role("button", name="担当者から外す").click()
    expect(page.locator(".message")).to_have_text("担当者が 1 人もいなくなるため、この操作はできません")

    row2.get_by_role("button", name="パスワード再設定").click()
    row2.locator('input[name="new_password"]').fill("1234567")
    row2.get_by_role("button", name="確定").click()
    expect(page.locator(FIELD_ERROR)).to_have_text("パスワードは 8 文字以上で入力してください")
    page.locator('tbody tr[data-employee-number="100002"] input[name="new_password"]').fill("newpass12")
    page.locator('tbody tr[data-employee-number="100002"]').get_by_role("button", name="確定").click()
    expect(page.locator(".message")).to_have_text("パスワードを再設定しました")
    other = new_page()
    login(other, server, "100002", "newpass12")
    expect(other.locator(".current-user")).to_have_text("佐藤 花子")

    add_equipment(page, server, "EQ-1", "椅子")
    page.goto(server + "/equipment/EQ-1/lend/")
    page.locator("#id_borrower").select_option(label="佐藤 花子（100002）")
    page.get_by_role("button", name="登録").click()
    page.goto(server + "/accounts/")
    page.locator('tbody tr[data-employee-number="100002"]').get_by_role("button", name="削除").click()
    expect(page.locator(".message")).to_have_text("この社員は備品を借りているため削除できません。先に返却を処理してください")
    page.goto(server + "/")
    page.locator('tbody tr[data-equipment-number="EQ-1"]').get_by_role("button", name="返却").click()
    page.goto(server + "/accounts/")
    page.locator('tbody tr[data-employee-number="100002"]').get_by_role("button", name="削除").click()
    expect(page.locator('tbody tr[data-employee-number="100002"]')).to_have_count(0)
    expect(page.locator(".message")).to_have_text("アカウントを削除しました")


def test_performance_50_users(data_dir):
    """備品 500 件、アカウント 50 件の状態で、同時に 50 人が貸出状況を開き、各表示が 3 秒以内か確かめる。"""
    connection = db.connect(str(data_dir))
    db.init_schema(connection)
    connection.execute("BEGIN IMMEDIATE")
    password_hash = generate_password_hash("password1")
    for i in range(50):
        connection.execute(
            "INSERT INTO accounts (employee_number, name, password_hash, is_manager) VALUES (?, ?, ?, ?)",
            (f"{100000 + i}", f"社員{i}", password_hash, 1 if i == 0 else 0),
        )
    for i in range(500):
        connection.execute(
            "INSERT INTO equipment (equipment_number, name, version) VALUES (?, ?, 1)",
            (f"EQ-{i:04d}", f"備品{i}"),
        )
    connection.execute("COMMIT")
    connection.close()
    with run_server(data_dir) as base:
        def fetch(_):
            started = time.time()
            with urlopen(base + "/", timeout=10) as response:
                response.read()
            return time.time() - started

        with ThreadPoolExecutor(max_workers=50) as pool:
            durations = list(pool.map(fetch, range(50)))
    assert max(durations) <= 3.0, f"最長 {max(durations):.2f} 秒"
