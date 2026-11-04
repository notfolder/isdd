"""前提データを画面操作で入れる。

data: {"accounts": [{"number", "name", "password"?, "staff"?}], "equipment": [{"number", "name"}],
       "lendings": [{"equipment", "borrower", "lent_on"}]}
accounts の 1 件目が最初の登録になり、契約どおり自動で担当者になる。2 件目以降の staff=True は、
最初の担当者がアカウントの一覧で「担当者にする」を押して付ける（段 3 の機能）。
"""

from support.config import BTN_MAKE_STAFF, BTN_UNMAKE_STAFF
from support.ui import account_row, click_with_dialog, equipment_row, login, register


class Seeder:
    def __init__(self, base_url: str, browser) -> None:
        self.base_url = base_url
        self.browser = browser

    def seed(self, data: dict) -> None:
        accounts = data.get("accounts", [])
        equipment = data.get("equipment", [])
        lendings = data.get("lendings", [])
        context = self.browser.new_context()
        page = context.new_page()
        try:
            for a in accounts:
                register(page, self.base_url, a["number"], a["name"], a.get("password", "password1"))
            extra_staff = [a for a in accounts[1:] if a.get("staff")]
            if accounts and (equipment or lendings or extra_staff):
                first = accounts[0]
                login(page, self.base_url, first["number"], first.get("password", "password1"))
                names = {a["number"]: a["name"] for a in accounts}
                for a in extra_staff:
                    page.goto(f"{self.base_url}/accounts/")
                    click_with_dialog(page, account_row(page, a["number"]).get_by_role("button", name=BTN_MAKE_STAFF), True)
                    account_row(page, a["number"]).get_by_role("button", name=BTN_UNMAKE_STAFF).wait_for()
                for e in equipment:
                    page.goto(f"{self.base_url}/equipment/new/")
                    page.fill("#id_equipment_number", e["number"])
                    page.fill("#id_name", e["name"])
                    page.get_by_role("button", name="保存").click()
                    equipment_row(page, e["number"]).wait_for()
                for l in lendings:
                    page.goto(self.base_url)
                    equipment_row(page, l["equipment"]).get_by_role("button", name="貸出").click()
                    page.select_option("#id_borrower", label=f"{names[l['borrower']]}（{l['borrower']}）")
                    page.fill("#id_lent_on", l["lent_on"])
                    page.get_by_role("button", name="登録").click()
                    equipment_row(page, l["equipment"]).wait_for()
                page.get_by_role("button", name="ログアウト").click()
        finally:
            context.close()
