"""E2E テストで使う操作の部品（アカウント登録、ログイン、備品の登録）。"""


def register(page, base: str, employee_number: str, name: str, password: str) -> None:
    page.goto(base + "/accounts/register/")
    page.fill("#id_employee_number", employee_number)
    page.fill("#id_name", name)
    page.fill("#id_password", password)
    page.get_by_role("button", name="登録").click()


def login(page, base: str, employee_number: str, password: str) -> None:
    page.goto(base + "/login/")
    page.fill("#id_employee_number", employee_number)
    page.fill("#id_password", password)
    page.get_by_role("button", name="ログイン").click()


def logout(page) -> None:
    page.get_by_role("button", name="ログアウト").click()


def add_equipment(page, base: str, number: str, name: str) -> None:
    page.goto(base + "/equipment/new/")
    page.fill("#id_equipment_number", number)
    page.fill("#id_name", name)
    page.get_by_role("button", name="保存").click()
