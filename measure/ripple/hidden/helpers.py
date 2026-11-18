"""段 4〜6 のテストで使う画面操作の補助（契約の id・文言だけに依存する）。"""

from playwright.sync_api import Locator, Page

from support.ui import click_with_dialog

BULK_DELETE = "選択したものを削除"


def click_any_dialog(page: Page, button: Locator) -> None:
    """確認ダイアログが出ても出なくても進める（出たら「はい」）。"""
    handler = lambda dialog: dialog.accept()  # noqa: E731
    page.on("dialog", handler)
    try:
        button.click()
        page.wait_for_load_state()
    finally:
        page.remove_listener("dialog", handler)


def bulk_delete(page: Page, rows: list) -> None:
    for row in rows:
        row.locator('input[name="selected"]').check()
    click_with_dialog(page, page.get_by_role("button", name=BULK_DELETE), True)
    page.wait_for_load_state()


def status_cell(row: Locator) -> Locator:
    return row.locator("td").nth(2)


def borrower_cell(row: Locator) -> Locator:
    return row.locator("td").nth(3)
