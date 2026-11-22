"""E2E テストで使う操作の手順（画面の id と文言は契約による）。"""

from datetime import datetime
from zoneinfo import ZoneInfo

from playwright.sync_api import expect

PASSWORD = "password1"


def today_jst() -> str:
    """日本時間の今日（YYYY-MM-DD）。"""
    return datetime.now(ZoneInfo("Asia/Tokyo")).date().isoformat()


def register(page, server, employee_number: str, name: str = "山田 太郎", password: str = PASSWORD) -> None:
    """アカウント登録画面で登録する（成功するとログイン画面へ移る）。"""
    page.goto(server.url("/accounts/register/"))
    page.locator("#id_employee_number").fill(employee_number)
    page.locator("#id_name").fill(name)
    page.locator("#id_password").fill(password)
    page.get_by_role("button", name="登録", exact=True).click()
    expect(page.locator(".message")).to_have_text("登録しました。ログインしてください")


def login(page, server, employee_number: str, password: str = PASSWORD) -> None:
    """ログイン画面でログインする。"""
    page.goto(server.url("/login/"))
    page.locator("#id_employee_number").fill(employee_number)
    page.locator("#id_password").fill(password)
    page.get_by_role("button", name="ログイン", exact=True).click()


def logout(page) -> None:
    """ログアウトボタンを押す。"""
    page.get_by_role("button", name="ログアウト", exact=True).click()
    expect(page.locator(".message")).to_have_text("ログアウトしました")


def create_equipment(page, server, number: str, name: str) -> None:
    """備品の登録画面から備品を 1 件登録する（担当者でログイン済みであること）。"""
    page.goto(server.url("/equipment/new/"))
    page.locator("#id_equipment_number").fill(number)
    page.locator("#id_name").fill(name)
    page.get_by_role("button", name="保存", exact=True).click()
    expect(page.locator(".message")).to_have_text("備品を登録しました")


def row(page, number: str):
    """貸出状況の表の、管理番号に対応する行。"""
    return page.locator(f'tbody tr[data-equipment-number="{number}"]')


def go_status(page, server) -> None:
    """貸出状況（トップ）を開く。"""
    page.goto(server.url("/"))


def lend_from_status(page, server, number: str, borrower_label: str, lent_on: str | None = None) -> None:
    """貸出状況の行の「貸出」から、借りる社員と貸出日を選んで登録する。"""
    go_status(page, server)
    row(page, number).get_by_role("button", name="貸出", exact=True).click()
    page.select_option("#id_borrower", label=borrower_label)
    if lent_on is not None:
        page.locator("#id_lent_on").fill(lent_on)
    page.get_by_role("button", name="登録", exact=True).click()
    expect(page.locator(".message")).to_have_text("貸出を登録しました")
