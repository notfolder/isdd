"""アカウント・ログイン・担当者に関する E2E テスト。"""

import sys
from pathlib import Path as _Path
_HERE = _Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


import time
import unittest

from support import AppServer, Client, seed_accounts, equipment_id


def register(client: Client, number: str, name: str, password: str):
    page = client.get("/accounts/register/")
    return client.submit(page, "登録", {"employee_number": number, "name": name, "password": password})


def login(client: Client, number: str, password: str):
    page = client.get("/login/")
    return client.submit(page, "ログイン", {"employee_number": number, "password": password})


class TestRegisterAccounts(unittest.TestCase):
    def setUp(self) -> None:
        self.server = AppServer().start()
        self.addCleanup(self.server.stop)

    def test_register_accounts(self) -> None:
        client = Client(self.server)
        page = register(client, "123456", "山田 太郎", "password1")
        self.assertTrue(page.has_text("登録しました。ログインしてください"))
        self.assertIsNotNone(page.by_id("id_employee_number"))
        page = login(client, "123456", "password1")
        self.assertEqual(page.by_class("current-user"), ["山田 太郎"])
        accounts = client.get("/accounts/")
        self.assertEqual(accounts.cells("data-employee-number", "123456")[2], "担当者")

        second = Client(self.server)
        register(second, "654321", "佐藤 花子", "password2")
        page = client.get("/accounts/")
        self.assertEqual(page.cells("data-employee-number", "654321")[2], "社員")

        page = register(Client(self.server), "12345", "名前", "password1")
        self.assertIn("社員番号は 6 桁の数字で入力してください", page.by_class("field-error"))
        self.assertEqual(page.by_id("id_employee_number").attrs.get("value"), "12345")
        page = register(Client(self.server), "111111", "", "password1")
        self.assertIn("名前を入力してください", page.by_class("field-error"))
        page = register(Client(self.server), "111111", "あ" * 31, "password1")
        self.assertIn("名前は 30 文字以内で入力してください", page.by_class("field-error"))
        page = register(Client(self.server), "111111", "名前", "1234567")
        self.assertIn("パスワードは 8 文字以上で入力してください", page.by_class("field-error"))
        page = register(Client(self.server), "123456", "重複", "password1")
        self.assertIn("この社員番号は既に登録されています", page.by_class("field-error"))

    def test_register_accounts_limit(self) -> None:
        seed_accounts(self.server, [f"9{i:05d}" for i in range(50)])
        page = register(Client(self.server), "100000", "上限", "password1")
        self.assertIn("利用者は 50 人までのため、登録できません", page.by_class("error"))


class TestLoginLogout(unittest.TestCase):
    def setUp(self) -> None:
        self.server = AppServer().start()
        self.addCleanup(self.server.stop)
        register(Client(self.server), "123456", "山田 太郎", "password1")

    def test_login_logout(self) -> None:
        client = Client(self.server)
        wrong_number = login(client, "999999", "password1")
        wrong_password = login(client, "123456", "wrongpass")
        expected = "社員番号またはパスワードが違います"
        self.assertEqual(wrong_number.by_class("error"), [expected])
        self.assertEqual(wrong_password.by_class("error"), [expected])
        self.assertEqual(wrong_number.by_id("id_employee_number").attrs.get("value"), "999999")
        page = login(client, "123456", "password1")
        self.assertEqual(page.by_class("current-user"), ["山田 太郎"])
        page = client.submit(page, "ログアウト")
        self.assertEqual(page.by_class("current-user"), [])
        self.assertTrue(page.has_text("ログイン"))


class TestIdleLogout(unittest.TestCase):
    def test_idle_logout(self) -> None:
        server = AppServer(idle_timeout_seconds=2).start()
        self.addCleanup(server.stop)
        register(Client(server), "123456", "山田 太郎", "password1")
        client = Client(server)
        login(client, "123456", "password1")
        self.assertEqual(client.get("/").by_class("current-user"), ["山田 太郎"])
        time.sleep(3)
        page = client.get("/")
        self.assertEqual(page.by_class("current-user"), [])
        page = client.get("/equipment/new/")
        self.assertIsNotNone(page.by_id("id_employee_number"))


class TestManageAccounts(unittest.TestCase):
    def setUp(self) -> None:
        self.server = AppServer().start()
        self.addCleanup(self.server.stop)
        register(Client(self.server), "123456", "山田 太郎", "password1")
        register(Client(self.server), "654321", "佐藤 花子", "password2")
        self.manager = Client(self.server)
        login(self.manager, "123456", "password1")

    def test_reset_password(self) -> None:
        page = self.manager.get("/accounts/")
        page = self.manager.submit(page, "パスワード再設定", must_contain="654321")
        self.assertTrue(any(e.attrs.get("name") == "new_password" for e in page.elements))
        page = self.manager.submit(page, "確定", {"new_password": "short"}, must_contain="654321")
        self.assertIn("パスワードは 8 文字以上で入力してください", page.by_class("field-error"))
        page = self.manager.get("/accounts/")
        page = self.manager.submit(page, "パスワード再設定", must_contain="654321")
        page = self.manager.submit(page, "確定", {"new_password": "newpass123"}, must_contain="654321")
        self.assertTrue(page.has_text("パスワードを再設定しました"))
        member = Client(self.server)
        page = login(member, "654321", "newpass123")
        self.assertEqual(page.by_class("current-user"), ["佐藤 花子"])

    def test_manage_manager_role(self) -> None:
        top = self.manager.get("/")
        self.assertTrue(top.has_text("備品を登録"))
        page = self.manager.get("/accounts/")
        page = self.manager.submit(page, "担当者にする", must_contain="654321")
        self.assertEqual(page.cells("data-employee-number", "654321")[2], "担当者")
        page = self.manager.submit(page, "担当者から外す", must_contain="654321")
        self.assertEqual(page.cells("data-employee-number", "654321")[2], "社員")
        page = self.manager.submit(page, "担当者から外す", must_contain="123456")
        self.assertIn("担当者が 1 人もいなくなるため、この操作はできません", page.by_class("error"))
        self.assertEqual(page.cells("data-employee-number", "123456")[2], "担当者")

    def test_delete_account(self) -> None:
        self.manager.post("/equipment/new/", {"equipment_number": "EQ-0001", "name": "ノート"})
        self.manager.post(f"/equipment/{equipment_id(self.server, 'EQ-0001')}/lend/",
                          {"borrower": "654321", "lent_on": "2000-01-01"})
        page = self.manager.get("/accounts/")
        page = self.manager.submit(page, "削除", must_contain="654321")
        self.assertIn("この社員は備品を借りているため削除できません。先に返却を処理してください",
                      page.by_class("error"))
        self.assertIsNotNone(page.row("data-employee-number", "654321"))
        seed_accounts(self.server, ["777777"])
        page = self.manager.get("/accounts/")
        page = self.manager.submit(page, "削除", must_contain="777777")
        self.assertIsNone(page.row("data-employee-number", "777777"))

    def test_access_ends_on_reset_and_delete(self) -> None:
        self.manager.post("/equipment/new/", {"equipment_number": "EQ-0001", "name": "ノート"})
        page = self.manager.get("/accounts/")
        page = self.manager.submit(page, "パスワード再設定", must_contain="654321")
        page = self.manager.submit(page, "確定", {"new_password": "newpass123"}, must_contain="654321")
        self.assertTrue(page.has_text("パスワードを再設定しました"))
        page = login(Client(self.server), "654321", "password2")
        self.assertIn("社員番号またはパスワードが違います", page.by_class("error"))
        seed_accounts(self.server, ["777777"])
        page = self.manager.get("/accounts/")
        page = self.manager.submit(page, "削除", must_contain="777777")
        self.assertIsNone(page.row("data-employee-number", "777777"))
        page = login(Client(self.server), "777777", "password1")
        self.assertIn("社員番号またはパスワードが違います", page.by_class("error"))
        page = self.manager.get(f"/equipment/{equipment_id(self.server, 'EQ-0001')}/lend/")
        self.assertTrue(page.has_text("佐藤 花子（654321）"))
        self.assertFalse(page.has_text("777777"))


if __name__ == "__main__":
    unittest.main()
