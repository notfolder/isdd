"""画面操作の補助（契約の id・文言だけに依存する）。"""

import re

from playwright.sync_api import Locator, Page, expect


def login(page: Page, base_url: str, number: str, password: str = "password1") -> None:
    page.goto(f"{base_url}/login/")
    page.fill("#id_employee_number", number)
    page.fill("#id_password", password)
    page.get_by_role("button", name="ログイン").click()


def register(page: Page, base_url: str, number: str, name: str, password: str = "password1") -> None:
    page.goto(f"{base_url}/accounts/register/")
    page.fill("#id_employee_number", number)
    page.fill("#id_name", name)
    page.fill("#id_password", password)
    page.get_by_role("button", name="登録").click()


def field_error(page: Page, input_id: str) -> Locator:
    return page.locator(".field", has=page.locator(f"#{input_id}")).locator(".field-error")


def equipment_row(page: Page, number: str) -> Locator:
    return page.locator(f'tr[data-equipment-number="{number}"]')


def account_row(page: Page, number: str) -> Locator:
    return page.locator(f'tr[data-employee-number="{number}"]')


def click_with_dialog(page: Page, button: Locator, accept: bool) -> None:
    page.once("dialog", lambda dialog: dialog.accept() if accept else dialog.dismiss())
    button.click()


def messages(page: Page) -> Locator:
    return page.locator(".message")


def add_equipment(page: Page) -> Locator:
    """「備品を登録」の入口。契約はボタンかリンクかを定めていないので両方を受け付ける。"""
    return page.get_by_role("button", name="備品を登録").or_(page.get_by_role("link", name="備品を登録"))


def expect_url(page: Page, base_url: str, path: str) -> None:
    """契約の URL に移ったか。クエリ文字列（?msg=... など）は付いていてもよい。"""
    expect(page).to_have_url(re.compile("^" + re.escape(f"{base_url}{path}") + r"(\?.*)?$"))
