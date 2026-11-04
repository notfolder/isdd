"""画面と権限の結合テスト（Flask のテストクライアント）。"""

import unittest

from src import accounts, db, equipment
from src.web import create_app
from tests.helpers import make_data_dir


class WebTest(unittest.TestCase):
    def setUp(self):
        self.data_dir = make_data_dir()
        self.app = create_app({
            "port": 0,
            "data_dir": self.data_dir,
            "session_idle_timeout_seconds": 1800,
        })
        self.client = self.app.test_client()
        conn = db.connect(self.data_dir)
        accounts.register_account(conn, "000001", "担当", "password1")
        accounts.register_account(conn, "000002", "社員", "password2")
        conn.close()

    def login(self, number, password):
        return self.client.post("/login/", data={"employee_number": number, "password": password})

    def test_status_page_anonymous_shows_links_and_no_buttons(self):
        response = self.client.get("/")
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('href="/login/"', html)
        self.assertIn('href="/accounts/register/"', html)
        self.assertNotIn("ログアウト", html)
        self.assertIn("備品は登録されていません", html)

    def test_login_failure_message_does_not_say_which_part_is_wrong(self):
        response = self.login("000001", "wrong-pass")
        html = response.get_data(as_text=True)
        self.assertIn('class="error"', html)
        self.assertIn("社員番号またはパスワードが違います", html)
        self.assertIn('value="000001"', html)

    def test_login_then_status_shows_name_and_logout(self):
        self.assertEqual(self.login("000001", "password1").status_code, 302)
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn('class="current-user"', html)
        self.assertIn("担当", html)
        self.assertIn("ログアウト", html)
        self.assertIn("備品を登録", html)

    def test_employee_does_not_see_manager_buttons(self):
        self.login("000002", "password2")
        html = self.client.get("/").get_data(as_text=True)
        self.assertNotIn("備品を登録", html)
        self.assertNotIn("削除", html)

    def test_anonymous_equipment_new_redirects_to_login(self):
        response = self.client.get("/equipment/new/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.headers["Location"])

    def test_employee_equipment_post_is_refused_and_no_data_changes(self):
        self.login("000002", "password2")
        response = self.client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "x"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("notice=manager_only", response.headers["Location"])
        follow = self.client.get(response.headers["Location"]).get_data(as_text=True)
        self.assertIn("この操作は担当者だけが行えます", follow)
        conn = db.connect(self.data_dir)
        self.assertEqual(equipment.list_equipment(conn), [])
        conn.close()

    def test_manager_creates_and_form_keeps_values_on_error(self):
        self.login("000001", "password1")
        ok = self.client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "ノート"})
        self.assertEqual(ok.status_code, 302)
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn('data-equipment-number="A-1"', html)
        self.assertIn("空き", html)
        bad = self.client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "重複"})
        html = bad.get_data(as_text=True)
        self.assertIn('class="field-error"', html)
        self.assertIn("この管理番号は既に使われています", html)
        self.assertIn('value="A-1"', html)

    def test_manager_update_and_delete_missing_equipment(self):
        self.login("000001", "password1")
        self.client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "ノート"})
        response = self.client.post("/equipment/A-1/edit/", data={"equipment_number": "A-1", "name": "新"})
        self.assertEqual(response.status_code, 302)
        response = self.client.post("/equipment/NONE/delete/")
        self.assertIn("notice=not_found", response.headers["Location"])

    def test_logout_clears_session(self):
        self.login("000001", "password1")
        self.client.post("/logout/")
        html = self.client.get("/").get_data(as_text=True)
        self.assertNotIn("ログアウト", html)

    def test_register_success_goes_to_login_with_notice(self):
        response = self.client.post(
            "/accounts/register/", data={"employee_number": "000003", "name": "新人", "password": "password3"}
        )
        self.assertEqual(response.status_code, 302)
        follow = self.client.get(response.headers["Location"]).get_data(as_text=True)
        self.assertIn("登録しました。ログインしてください", follow)

    def test_register_errors_keep_values(self):
        response = self.client.post(
            "/accounts/register/", data={"employee_number": "12", "name": "", "password": "short"}
        )
        html = response.get_data(as_text=True)
        self.assertEqual(html.count('class="field-error"'), 3)
        self.assertIn("社員番号は 6 桁の数字で入力してください", html)
        self.assertIn("名前を入力してください", html)
        self.assertIn("パスワードは 8 文字以上で入力してください", html)
        self.assertIn('value="12"', html)


if __name__ == "__main__":
    unittest.main()
