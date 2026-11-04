"""画面と権限の結合テスト（Flask のテストクライアント）。"""

import re
import unittest

from src import accounts, db, equipment, lending
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
        accounts.register_account(conn, "0000001", "担当", "password1")
        accounts.register_account(conn, "0000002", "社員", "password2")
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
        response = self.login("0000001", "wrong-pass")
        html = response.get_data(as_text=True)
        self.assertIn('class="error"', html)
        self.assertIn("社員番号またはパスワードが違います", html)
        self.assertIn('value="0000001"', html)

    def test_login_then_status_shows_name_and_logout(self):
        self.assertEqual(self.login("0000001", "password1").status_code, 302)
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn('class="current-user"', html)
        self.assertIn("担当", html)
        self.assertIn("ログアウト", html)
        self.assertIn("備品を登録", html)

    def test_employee_does_not_see_manager_buttons(self):
        self.login("0000002", "password2")
        html = self.client.get("/").get_data(as_text=True)
        self.assertNotIn("備品を登録", html)
        self.assertNotIn("削除", html)

    def test_anonymous_equipment_new_redirects_to_login(self):
        response = self.client.get("/equipment/new/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.headers["Location"])

    def test_employee_equipment_post_is_refused_and_no_data_changes(self):
        self.login("0000002", "password2")
        response = self.client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "x"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("notice=manager_only", response.headers["Location"])
        follow = self.client.get(response.headers["Location"]).get_data(as_text=True)
        self.assertIn("この操作は担当者だけが行えます", follow)
        conn = db.connect(self.data_dir)
        self.assertEqual(equipment.list_equipment(conn), [])
        conn.close()

    def test_manager_creates_and_form_keeps_values_on_error(self):
        self.login("0000001", "password1")
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
        self.login("0000001", "password1")
        self.client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "ノート"})
        page = self.client.get("/equipment/A-1/edit/").get_data(as_text=True)
        token = re.search(r'name="loaded_updated_at" value="([^"]+)"', page).group(1)
        response = self.client.post(
            "/equipment/A-1/edit/",
            data={"equipment_number": "A-1", "name": "新", "loaded_updated_at": token},
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.post("/equipment/NONE/delete/")
        self.assertIn("notice=not_found", response.headers["Location"])

    def test_stale_update_is_refused_with_error(self):
        self.login("0000001", "password1")
        self.client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "ノート"})
        page = self.client.get("/equipment/A-1/edit/").get_data(as_text=True)
        token = re.search(r'name="loaded_updated_at" value="([^"]+)"', page).group(1)
        self.client.post(
            "/equipment/A-1/edit/",
            data={"equipment_number": "A-1", "name": "先の変更", "loaded_updated_at": token},
        )
        response = self.client.post(
            "/equipment/A-1/edit/",
            data={"equipment_number": "A-1", "name": "遅れた変更", "loaded_updated_at": token},
        )
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('<p class="error">他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください</p>', html)
        self.assertIn('value="遅れた変更"', html)
        conn = db.connect(self.data_dir)
        self.assertEqual(equipment.get_equipment(conn, "A-1")["name"], "先の変更")
        conn.close()

    def test_lend_return_flow_and_status_columns(self):
        self.login("0000001", "password1")
        self.client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "ノート"})
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn('action="/equipment/A-1/lend/"', html)
        form = self.client.get("/equipment/A-1/lend/").get_data(as_text=True)
        self.assertIn("備品: A-1 ノート", form)
        self.assertIn("社員（0000002）", form)
        response = self.client.post(
            "/equipment/A-1/lend/", data={"borrower": "0000002", "lent_on": lending.today_jst().isoformat()}
        )
        self.assertEqual(response.status_code, 302)
        html = self.client.get(response.headers["Location"]).get_data(as_text=True)
        self.assertIn("貸出を登録しました", html)
        self.assertIn("貸出中", html)
        self.assertIn("社員", html)
        self.assertIn(lending.today_jst().isoformat(), html)
        second = self.client.post("/equipment/A-1/lend/", data={"borrower": "0000001", "lent_on": "2020-01-01"})
        self.assertIn("notice=already_lent", second.headers["Location"])
        response = self.client.post("/equipment/A-1/return/")
        self.assertIn("notice=returned", response.headers["Location"])
        html = self.client.get(response.headers["Location"]).get_data(as_text=True)
        self.assertIn("返却を処理しました", html)
        again = self.client.post("/equipment/A-1/return/")
        self.assertIn("notice=already_returned", again.headers["Location"])

    def test_lend_form_rejects_missing_borrower_and_future_date(self):
        self.login("0000001", "password1")
        self.client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "ノート"})
        response = self.client.post("/equipment/A-1/lend/", data={"borrower": "", "lent_on": "2999-01-01"})
        html = response.get_data(as_text=True)
        self.assertIn("借りる社員を選んでください", html)
        self.assertIn("貸出日に未来の日付は入力できません", html)
        self.assertEqual(html.count('class="field-error"'), 2)
        self.assertIn('value="2999-01-01"', html)

    def test_employee_and_anonymous_cannot_lend_or_return(self):
        self.login("0000001", "password1")
        self.client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "ノート"})
        self.client.post("/logout/")
        response = self.client.post("/equipment/A-1/return/")
        self.assertIn("/login/", response.headers["Location"])
        response = self.client.post("/equipment/A-1/lend/", data={"borrower": "0000002", "lent_on": "2020-01-01"})
        self.assertIn("/login/", response.headers["Location"])
        self.login("0000002", "password2")
        response = self.client.post("/equipment/A-1/lend/", data={"borrower": "0000002", "lent_on": "2020-01-01"})
        self.assertIn("notice=manager_only", response.headers["Location"])
        conn = db.connect(self.data_dir)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM lendings").fetchone()[0], 0)
        conn.close()

    def test_delete_of_lent_equipment_is_refused_with_message(self):
        self.login("0000001", "password1")
        self.client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "ノート"})
        self.client.post("/equipment/A-1/lend/", data={"borrower": "0000002", "lent_on": "2020-01-01"})
        response = self.client.post("/equipment/A-1/delete/")
        self.assertIn("notice=delete_lent", response.headers["Location"])
        html = self.client.get(response.headers["Location"]).get_data(as_text=True)
        self.assertIn("この備品は貸出中のため削除できません。先に返却を処理してください", html)
        conn = db.connect(self.data_dir)
        self.assertIsNotNone(equipment.get_equipment(conn, "A-1"))
        conn.close()

    def test_anonymous_status_shows_lending_without_buttons(self):
        self.login("0000001", "password1")
        self.client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "ノート"})
        self.client.post("/equipment/A-1/lend/", data={"borrower": "0000002", "lent_on": "2020-01-01"})
        self.client.post("/logout/")
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("2020-01-01", html)
        self.assertNotIn("<button", html)

    def test_logout_clears_session(self):
        self.login("0000001", "password1")
        self.client.post("/logout/")
        html = self.client.get("/").get_data(as_text=True)
        self.assertNotIn("ログアウト", html)

    def test_register_success_goes_to_login_with_notice(self):
        response = self.client.post(
            "/accounts/register/", data={"employee_number": "0000003", "name": "新人", "password": "password3"}
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
        self.assertIn("社員番号は 7 桁の数字で入力してください", html)
        self.assertIn("名前を入力してください", html)
        self.assertIn("パスワードは 8 文字以上で入力してください", html)
        self.assertIn('value="12"', html)


if __name__ == "__main__":
    unittest.main()
