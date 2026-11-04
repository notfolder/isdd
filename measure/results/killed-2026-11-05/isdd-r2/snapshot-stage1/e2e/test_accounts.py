"""アカウントとログインの E2E テスト。実行: 詳細設計書 8-4 のコマンド。"""

import time

from e2e.support import LedgerE2ECase, seed_accounts


class AccountE2E(LedgerE2ECase):
    """アカウント登録・ログイン・ログアウトの画面操作を確かめる。"""

    def test_register_first_account(self):
        # アカウントが 0 件なら担当者になる
        self.register("000001", "担当 太郎", "password1")
        self.assertEqual(self.page.locator(".message").inner_text(), "登録しました。ログインしてください")
        self.login("000001", "password1")
        self.assertEqual(self.page.locator(".current-user").inner_text(), "担当 太郎")
        self.assertTrue(self.page.get_by_role("link", name="備品を登録").is_visible())

    def test_register_second_account_is_employee(self):
        # 2 件目以降は社員になる
        seed_accounts(self.data_dir, [("000001", "担当", "password1")])
        self.register("000002", "社員 花子", "password2")
        self.login("000002", "password2")
        self.assertEqual(self.page.locator(".current-user").inner_text(), "社員 花子")
        self.assertEqual(self.page.get_by_role("link", name="備品を登録").count(), 0)
        self.assertEqual(self.page.get_by_role("button", name="削除").count(), 0)

    def test_account_input_validation(self):
        # 入力の検査と、入力値を消さないこと
        seed_accounts(self.data_dir, [("000001", "担当", "password1")])
        self.open("/accounts/register/")
        self.page.fill("#id_employee_number", "12345")
        self.page.fill("#id_name", "")
        self.page.fill("#id_password", "short")
        self.page.get_by_role("button", name="登録").click()
        errors = self.page.locator(".field .field-error").all_inner_texts()
        self.assertEqual(
            errors,
            [
                "社員番号は 6 桁の数字で入力してください",
                "名前を入力してください",
                "パスワードは 8 文字以上で入力してください",
            ],
        )
        self.assertEqual(self.page.input_value("#id_employee_number"), "12345")
        self.page.fill("#id_employee_number", "000001")
        self.page.fill("#id_name", "a" * 31)
        self.page.fill("#id_password", "password1")
        self.page.get_by_role("button", name="登録").click()
        self.assertEqual(
            self.page.locator(".field .field-error").inner_text(), "名前は 30 文字以内で入力してください"
        )
        self.page.fill("#id_name", "同じ番号")
        self.page.get_by_role("button", name="登録").click()
        self.assertEqual(
            self.page.locator(".field .field-error").inner_text(), "この社員番号は既に登録されています"
        )

    def test_login_success_and_failure(self):
        # 成功でトップに戻り、失敗では違いを示さない
        seed_accounts(self.data_dir, [("000001", "担当", "password1")])
        self.open("/login/")
        self.page.fill("#id_employee_number", "000001")
        self.page.fill("#id_password", "wrong-pass")
        self.page.get_by_role("button", name="ログイン").click()
        self.assertEqual(self.page.locator(".error").inner_text(), "社員番号またはパスワードが違います")
        self.assertEqual(self.page.input_value("#id_employee_number"), "000001")
        self.login("000001", "password1")
        self.assertEqual(self.page.locator(".current-user").inner_text(), "担当")

    def test_logout(self):
        # ログアウトすると未ログインの表示に戻る
        seed_accounts(self.data_dir, [("000001", "担当", "password1")])
        self.login("000001", "password1")
        self.page.get_by_role("button", name="ログアウト").click()
        self.page.wait_for_url(self.base + "/")
        self.assertEqual(self.page.get_by_role("link", name="ログイン").count(), 1)
        self.assertEqual(self.page.locator(".current-user").count(), 0)


class AutoLogoutE2E(LedgerE2ECase):
    """無操作の自動ログアウトだけを、短い秒数で確かめる。"""

    idle_timeout_seconds = 2

    def prepare_data(self):
        seed_accounts(self.data_dir, [("000001", "担当", "password1")])

    def test_auto_logout_after_idle(self):
        # 無操作が設定時間を超えると自動でログアウトする
        self.login("000001", "password1")
        self.assertEqual(self.page.locator(".current-user").inner_text(), "担当")
        time.sleep(3)
        self.open("/")
        self.assertEqual(self.page.locator(".current-user").count(), 0)
        self.assertEqual(self.page.get_by_role("link", name="ログイン").count(), 1)
