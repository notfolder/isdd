"""E2E テストの操作の補助関数（画面の操作を組み合わせる）。"""


def register(page, base, number, name, password="password1"):
    page.goto(base + "/accounts/register/")
    page.fill("#id_employee_number", number)
    page.fill("#id_name", name)
    page.fill("#id_password", password)
    page.get_by_role("button", name="登録").click()


def login(page, base, number, password="password1"):
    page.goto(base + "/login/")
    page.fill("#id_employee_number", number)
    page.fill("#id_password", password)
    page.get_by_role("button", name="ログイン").click()


def logout(page):
    page.get_by_role("button", name="ログアウト").click()


def create_equipment(page, base, number, name):
    page.goto(base + "/equipment/new/")
    page.fill("#id_equipment_number", number)
    page.fill("#id_name", name)
    page.get_by_role("button", name="保存").click()


def row(page, number):
    return page.locator(f'tbody tr[data-equipment-number="{number}"]')


def today_jst():
    """日本時間の今日を YYYY-MM-DD で返す（貸出日の既定値と同じ基準）。"""
    from datetime import datetime, timedelta, timezone

    return datetime.now(timezone(timedelta(hours=9))).date().isoformat()


def lend(page, base, number, borrower_label, lent_on=None):
    """貸出の登録画面を開き、借りる社員（表示の文言）と貸出日を入れて「登録」を押す。"""
    page.goto(base + f"/equipment/{number}/lend/")
    page.select_option("#id_borrower", label=borrower_label)
    if lent_on is not None:
        page.fill("#id_lent_on", lent_on)
    page.get_by_role("button", name="登録").click()


def new_manager_page(page):
    """同じ担当者アカウントを別のブラウザ（別の Cookie）で使う。同時の操作を再現するため。"""
    context = page.context.browser.new_context()
    other = context.new_page()
    other.set_default_timeout(10000)
    return other, context
