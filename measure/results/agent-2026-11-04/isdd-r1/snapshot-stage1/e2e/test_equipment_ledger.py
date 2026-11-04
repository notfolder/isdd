"""備品台帳の E2E テスト。実際に起動したサーバーに HTTP で要求し、返った HTML を確かめる。"""

import sqlite3
import sys
import time
import unittest
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from support import Client, Server  # noqa: E402

EMP_MANAGER = "000001"
EMP_MEMBER = "000002"
PASSWORD = "password1"
NAME_MANAGER = "山田太郎"
NAME_MEMBER = "佐藤花子"


class EquipmentLedgerE2E(unittest.TestCase):
    def setUp(self):
        self.servers = []

    def tearDown(self):
        for server in self.servers:
            server.stop()

    def start(self, idle_timeout_seconds: int = 1800) -> Server:
        server = Server(idle_timeout_seconds=idle_timeout_seconds)
        self.servers.append(server)
        return server

    def register(self, client: Client, employee: str, name: str, password: str = PASSWORD):
        return client.post(
            "/accounts/register/",
            {"employee_number": employee, "name": name, "password": password},
            follow=False,
        )

    def login(self, client: Client, employee: str, password: str = PASSWORD):
        return client.post("/login/", {"employee_number": employee, "password": password})

    def manager_with_equipment(self, server: Server, equipment=None) -> Client:
        """担当者を登録してログインし、備品を登録する。"""
        client = Client(server.base)
        self.register(client, EMP_MANAGER, NAME_MANAGER)
        self.login(client, EMP_MANAGER)
        for number, name in equipment or []:
            client.post("/equipment/new/", {"equipment_number": number, "name": name})
        return client

    # 16 件の E2E シナリオ（詳細設計書 8-2 の順）

    def test_register_first_account(self):
        server = self.start()
        client = Client(server.base)
        res = self.register(client, EMP_MANAGER, NAME_MANAGER)
        self.assertEqual(res.status, 302)
        page = client.get("/login/").page
        self.assertIn("登録しました。ログインしてください", page.texts("message"))
        res = self.login(client, EMP_MANAGER)
        self.assertEqual(res.path, "/")
        self.assertEqual(res.page.texts("current-user"), [NAME_MANAGER])
        self.assertTrue(res.page.has_link("備品を登録"))

    def test_register_second_account_as_member(self):
        server = self.start()
        client = Client(server.base)
        self.register(client, EMP_MANAGER, NAME_MANAGER)
        self.register(Client(server.base), EMP_MEMBER, NAME_MEMBER)
        page = self.login(client, EMP_MEMBER).page
        self.assertEqual(page.texts("current-user"), [NAME_MEMBER])
        self.assertFalse(page.has_link("備品を登録"))

    def test_register_account_validation(self):
        server = self.start()
        client = Client(server.base)
        self.register(client, EMP_MANAGER, NAME_MANAGER)
        res = client.post(
            "/accounts/register/",
            {"employee_number": "12345", "name": "", "password": "short"},
        )
        page = res.page
        self.assertIn("社員番号は 6 桁の数字で入力してください", page.field_errors("id_employee_number"))
        self.assertIn("名前を入力してください", page.field_errors("id_name"))
        self.assertIn("パスワードは 8 文字以上で入力してください", page.field_errors("id_password"))
        self.assertEqual(page.value_of("id_employee_number"), "12345")

        res = client.post(
            "/accounts/register/",
            {"employee_number": EMP_MANAGER, "name": "あ" * 31, "password": PASSWORD},
        )
        page = res.page
        self.assertIn("名前は 30 文字以内で入力してください", page.field_errors("id_name"))
        self.assertIn("この社員番号は既に登録されています", page.field_errors("id_employee_number"))
        self.assertEqual(page.value_of("id_name"), "あ" * 31)

    def test_login_and_logout(self):
        server = self.start()
        client = Client(server.base)
        self.register(client, EMP_MANAGER, NAME_MANAGER)
        page = self.login(client, EMP_MANAGER).page
        self.assertEqual(page.texts("current-user"), [NAME_MANAGER])
        self.assertTrue(page.has_button("ログアウト"))
        page = client.post("/logout/").page
        self.assertEqual(page.texts("current-user"), [])
        self.assertTrue(page.has_link("ログイン"))
        self.assertTrue(page.has_link("アカウント登録"))

    def test_login_failure_no_hint(self):
        server = self.start()
        client = Client(server.base)
        self.register(client, EMP_MANAGER, NAME_MANAGER)
        message = "社員番号またはパスワードが違います"
        page = self.login(Client(server.base), EMP_MANAGER, "wrongpass").page
        self.assertEqual(page.texts("error"), [message])
        page = self.login(Client(server.base), "999999", PASSWORD).page
        self.assertEqual(page.texts("error"), [message])
        self.assertEqual(page.value_of("id_employee_number"), "999999")

    def test_auto_logout_after_idle(self):
        server = self.start(idle_timeout_seconds=2)
        client = Client(server.base)
        self.register(client, EMP_MANAGER, NAME_MANAGER)
        self.login(client, EMP_MANAGER)
        time.sleep(3)
        res = client.get("/equipment/new/")
        self.assertEqual(res.path, "/login/")
        self.assertIn("一定時間操作がなかったため、ログアウトしました", res.page.texts("message"))
        self.assertEqual(client.get("/").page.texts("current-user"), [])

    def test_manager_register_equipment(self):
        server = self.start()
        client = self.manager_with_equipment(server)
        res = client.post("/equipment/new/", {"equipment_number": "PC-0001", "name": "ノートPC"})
        self.assertEqual(res.path, "/")
        self.assertIn("備品を登録しました", res.page.texts("message"))
        rows = res.page.rows()
        self.assertEqual([r.attrs["data-equipment-number"] for r in rows], ["PC-0001"])
        cells = [td.text for td in rows[0].children if td.tag == "td"]
        self.assertEqual(cells[:3], ["PC-0001", "ノートPC", "空き"])

        res = client.post("/equipment/new/", {"equipment_number": "PC-0001", "name": "別の品"})
        self.assertIn("この管理番号は既に使われています", res.page.field_errors("id_equipment_number"))
        self.assertEqual(res.page.value_of("id_equipment_number"), "PC-0001")

    def test_equipment_validation(self):
        server = self.start()
        client = self.manager_with_equipment(server)
        res = client.post("/equipment/new/", {"equipment_number": "ＰＣ0001", "name": ""})
        self.assertIn(
            "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください",
            res.page.field_errors("id_equipment_number"),
        )
        self.assertIn("備品名を入力してください", res.page.field_errors("id_name"))
        res = client.post("/equipment/new/", {"equipment_number": "A" * 21, "name": "x" * 51})
        self.assertIn(
            "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください",
            res.page.field_errors("id_equipment_number"),
        )
        self.assertIn("備品名は 50 文字以内で入力してください", res.page.field_errors("id_name"))
        self.assertEqual(client.get("/").page.rows(), [])

    def test_manager_edit_equipment(self):
        server = self.start()
        client = self.manager_with_equipment(server, [("PC-0001", "ノートPC"), ("PC-0002", "プロジェクタ")])
        page = client.get("/equipment/PC-0001/edit/").page
        self.assertEqual(page.value_of("id_equipment_number"), "PC-0001")
        res = client.post("/equipment/PC-0001/edit/", {"equipment_number": "PC-0001", "name": "ノートPC B"})
        self.assertEqual(res.path, "/")
        self.assertIn("備品を保存しました", res.page.texts("message"))
        self.assertIn("ノートPC B", [c.text for r in res.page.rows() for c in r.children if c.tag == "td"])

        res = client.post("/equipment/PC-0001/edit/", {"equipment_number": "PC-0002", "name": "変更"})
        self.assertIn("この管理番号は既に使われています", res.page.field_errors("id_equipment_number"))
        rows = client.get("/").page.rows()
        self.assertEqual([r.attrs["data-equipment-number"] for r in rows], ["PC-0001", "PC-0002"])

    def test_manager_delete_equipment(self):
        server = self.start()
        client = self.manager_with_equipment(server, [("PC-0001", "ノートPC")])
        page = client.get("/").page
        forms = [n for n in page.all(tag="form") if n.attrs.get("action") == "/equipment/PC-0001/delete/"]
        self.assertEqual(len(forms), 1)
        self.assertIn("confirm(", forms[0].attrs.get("onsubmit", ""))
        res = client.post("/equipment/PC-0001/delete/")
        self.assertIn("備品を削除しました", res.page.texts("message"))
        self.assertEqual(client.get("/").page.rows(), [])

    def test_member_cannot_operate_equipment(self):
        server = self.start()
        manager = self.manager_with_equipment(server, [("PC-0001", "ノートPC")])
        self.register(Client(server.base), EMP_MEMBER, NAME_MEMBER)
        member = Client(server.base)
        self.login(member, EMP_MEMBER)
        message = "この操作は担当者だけが行えます"
        res = member.get("/equipment/new/")
        self.assertEqual(res.path, "/")
        self.assertIn(message, res.page.texts("message"))
        res = member.post("/equipment/PC-0001/delete/")
        self.assertIn(message, res.page.texts("message"))
        res = member.post("/equipment/PC-0001/edit/", {"equipment_number": "PC-9999", "name": "改ざん"})
        self.assertIn(message, res.page.texts("message"))
        rows = manager.get("/").page.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].attrs["data-equipment-number"], "PC-0001")
        self.assertNotIn("削除", member.get("/").page.buttons())

    def test_guest_cannot_operate_equipment(self):
        server = self.start()
        self.manager_with_equipment(server, [("PC-0001", "ノートPC")])
        guest = Client(server.base)
        res = guest.get("/equipment/new/")
        self.assertEqual(res.path, "/login/")
        res = guest.post("/equipment/PC-0001/delete/")
        self.assertEqual(res.path, "/login/")
        rows = Client(server.base).get("/").page.rows()
        self.assertEqual(len(rows), 1)

    def test_view_loan_status_as_guest(self):
        server = self.start()
        self.manager_with_equipment(server, [("PC-0002", "プロジェクタ"), ("PC-0001", "ノートPC A")])
        page = Client(server.base).get("/").page
        rows = page.rows()
        self.assertEqual([r.attrs["data-equipment-number"] for r in rows], ["PC-0001", "PC-0002"])
        cells = [[td.text for td in r.children if td.tag == "td"] for r in rows]
        self.assertEqual(cells[0][:3], ["PC-0001", "ノートPC A", "空き"])
        self.assertEqual(cells[1][:3], ["PC-0002", "プロジェクタ", "空き"])
        self.assertEqual(page.buttons(), [])
        self.assertTrue(page.has_link("ログイン"))
        self.assertTrue(page.has_link("アカウント登録"))

    def test_view_empty_loan_status(self):
        server = self.start()
        page = Client(server.base).get("/").page
        self.assertIn("備品は登録されていません", page.raw)
        self.assertEqual(page.rows(), [])

    def test_role_button_visibility(self):
        server = self.start()
        manager = self.manager_with_equipment(server, [("PC-0001", "ノートPC")])
        self.register(Client(server.base), EMP_MEMBER, NAME_MEMBER)
        member = Client(server.base)
        self.login(member, EMP_MEMBER)

        guest_page = Client(server.base).get("/").page
        self.assertFalse(guest_page.has_link("備品を登録"))
        self.assertEqual(guest_page.buttons(), [])

        member_page = member.get("/").page
        self.assertEqual(member_page.texts("current-user"), [NAME_MEMBER])
        self.assertFalse(member_page.has_link("備品を登録"))
        self.assertEqual(member_page.buttons(), ["ログアウト"])

        manager_page = manager.get("/").page
        self.assertTrue(manager_page.has_link("備品を登録"))
        self.assertEqual(sorted(manager_page.buttons()), ["ログアウト", "修正", "削除"])

    def test_list_response_time(self):
        server = self.start()
        self.manager_with_equipment(server)
        conn = sqlite3.connect(str(server.db_path()))
        conn.executemany(
            "INSERT INTO equipment (equipment_number, name) VALUES (?, ?)",
            [(f"EQ-{i:04d}", f"備品 {i}") for i in range(500)],
        )
        conn.commit()
        conn.close()
        started = time.time()
        with urllib.request.urlopen(server.base + "/", timeout=10) as res:
            body = res.read().decode("utf-8")
        elapsed = time.time() - started
        self.assertIn('data-equipment-number="EQ-0499"', body)
        self.assertLess(elapsed, 3.0)


if __name__ == "__main__":
    unittest.main()
