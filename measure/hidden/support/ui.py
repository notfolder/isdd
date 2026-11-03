"""画面操作の補助（契約の id・文言だけに依存する）。"""

from playwright.sync_api import Locator, Page


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
