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
