"""備品の貸出・返却と、修正・削除の貸出に関する E2E テスト。実行: 詳細設計書 8-4 のコマンド。"""

from datetime import timedelta

from src.lending import today_jst
from e2e.support import LedgerE2ECase, seed_accounts, seed_equipment, seed_lending

MANAGER = ("0000001", "担当", "password1")
EMPLOYEE = ("0000002", "社員", "password2")


class LendingE2E(LedgerE2ECase):
    """担当者による貸出・返却、同時の操作、修正と削除の制限。"""

    def prepare_data(self):
        seed_accounts(self.data_dir, [MANAGER, EMPLOYEE])
        seed_equipment(self.data_dir, [("A-1", "ノート")])

    def start_shared_session(self):
        """Cookie を共有する BrowserContext を作り、self.page をその中のページにする。戻り値は context。"""
        context = self.browser.new_context()
        self.page = context.new_page()
        return context

    def open_lend_form(self, page, number="A-1"):
        """貸出の登録画面を開く。"""
        page.goto(f"{self.base}/equipment/{number}/lend/")

    def test_lend_equipment(self):
        # 行の「貸出」から借りる社員を選び、貸出日は今日のまま登録する
        self.login(MANAGER[0], MANAGER[2])
        self.row("A-1").get_by_role("button", name="貸出").click()
        self.assertEqual(self.page.locator(".lending-equipment").inner_text(), "備品: A-1 ノート")
        self.page.select_option("#id_borrower", label=f"{EMPLOYEE[1]}（{EMPLOYEE[0]}）")
        self.page.get_by_role("button", name="登録").click()
        self.page.wait_for_url("**/?notice=lent")
        self.assertEqual(self.page.locator(".message").inner_text(), "貸出を登録しました")
        cells = self.row("A-1").locator("td").all_inner_texts()
        self.assertEqual(cells[:5], ["A-1", "ノート", "貸出中", EMPLOYEE[1], today_jst().isoformat()])

    def test_lend_validation(self):
        # 社員の未選択と未来の貸出日は入力欄のエラー。入力値は残り、登録されない
        self.login(MANAGER[0], MANAGER[2])
        self.open_lend_form(self.page)
        tomorrow_text = (today_jst() + timedelta(days=1)).isoformat()
        self.page.fill("#id_lent_on", tomorrow_text)
        self.page.get_by_role("button", name="登録").click()
        self.assertEqual(
            self.page.locator(".field .field-error").all_inner_texts(),
            ["借りる社員を選んでください", "貸出日に未来の日付は入力できません"],
        )
        self.assertEqual(self.page.input_value("#id_lent_on"), tomorrow_text)
        self.open("/")
        self.assertEqual(self.row("A-1").locator("td").nth(2).inner_text(), "空き")

    def test_lend_already_lent(self):
        # 2 つの画面で同じ備品の貸出を開き、先に貸した方だけが記録される
        context = self.start_shared_session()
        self.login(MANAGER[0], MANAGER[2])
        other = context.new_page()
        self.open_lend_form(self.page)
        self.open_lend_form(other)
        self.page.select_option("#id_borrower", label=f"{EMPLOYEE[1]}（{EMPLOYEE[0]}）")
        self.page.get_by_role("button", name="登録").click()
        self.page.wait_for_url("**/?notice=lent")
        other.select_option("#id_borrower", label=f"{MANAGER[1]}（{MANAGER[0]}）")
        other.get_by_role("button", name="登録").click()
        other.wait_for_url("**/?notice=already_lent")
        self.assertEqual(other.locator(".message").inner_text(), "この備品は既に貸出中です")
        self.assertEqual(self.row("A-1").locator("td").nth(3).inner_text(), EMPLOYEE[1])

    def test_return_equipment(self):
        # 返却の確認でキャンセルすると貸出中のまま。「はい」で空きに戻り、記録は残らない
        seed_lending(self.data_dir, [("A-1", EMPLOYEE[0], "2026-01-15")])
        self.login(MANAGER[0], MANAGER[2])
        self.page.once("dialog", lambda dialog: dialog.dismiss())
        self.row("A-1").get_by_role("button", name="返却").click()
        self.page.wait_for_timeout(300)
        self.assertEqual(self.row("A-1").locator("td").nth(2).inner_text(), "貸出中")
        self.page.once("dialog", lambda dialog: dialog.accept())
        self.row("A-1").get_by_role("button", name="返却").click()
        self.page.wait_for_url("**/?notice=returned")
        self.assertEqual(self.page.locator(".message").inner_text(), "返却を処理しました")
        cells = self.row("A-1").locator("td").all_inner_texts()
        self.assertEqual(cells[:5], ["A-1", "ノート", "空き", "", ""])

    def test_return_already_returned(self):
        # 同じ備品の返却を 2 つの画面で行うと、後の返却は既に返却済みとして扱う
        seed_lending(self.data_dir, [("A-1", EMPLOYEE[0], "2026-01-15")])
        context = self.start_shared_session()
        self.login(MANAGER[0], MANAGER[2])
        other = context.new_page()
        other.goto(self.base + "/")
        self.page.once("dialog", lambda dialog: dialog.accept())
        self.row("A-1").get_by_role("button", name="返却").click()
        self.page.wait_for_url("**/?notice=returned")
        other.once("dialog", lambda dialog: dialog.accept())
        other.locator("tbody tr").get_by_role("button", name="返却").click()
        other.wait_for_url("**/?notice=already_returned")
        self.assertEqual(other.locator(".message").inner_text(), "この備品は既に返却されています")

    def test_lending_operation_denied(self):
        # 社員は貸出の画面に入れず、直接の要求も拒否される。未ログインはログインへ移る。データは変わらない
        seed_lending(self.data_dir, [("A-1", EMPLOYEE[0], "2026-01-15")])
        self.login(EMPLOYEE[0], EMPLOYEE[2])
        self.open("/equipment/A-1/lend/")
        self.assertEqual(self.page.url, self.base + "/?notice=manager_only")
        self.assertEqual(self.page.locator(".message").inner_text(), "この操作は担当者だけが行えます")
        response = self.page.request.post(self.base + "/equipment/A-1/return/", max_redirects=0)
        self.assertEqual(response.status, 302)
        self.assertIn("notice=manager_only", response.headers["location"])
        self.open("/logout/")
        self.page.request.post(self.base + "/logout/", max_redirects=0)
        self.open("/equipment/A-1/lend/")
        self.assertIn("/login/", self.page.url)
        response = self.page.request.post(self.base + "/equipment/A-1/return/", max_redirects=0)
        self.assertIn("/login/", response.headers["location"])
        self.open("/")
        self.assertEqual(self.row("A-1").locator("td").nth(2).inner_text(), "貸出中")
        self.assertEqual(self.row("A-1").locator("td").nth(3).inner_text(), EMPLOYEE[1])

    def test_delete_lent_blocked(self):
        # 貸出中の備品は、確認で「はい」を選んでも削除されず、理由が出る
        seed_lending(self.data_dir, [("A-1", EMPLOYEE[0], "2026-01-15")])
        self.login(MANAGER[0], MANAGER[2])
        self.page.once("dialog", lambda dialog: dialog.accept())
        self.row("A-1").get_by_role("button", name="削除").click()
        self.page.wait_for_url("**/?notice=delete_lent")
        self.assertEqual(
            self.page.locator(".message").inner_text(),
            "この備品は貸出中のため削除できません。先に返却を処理してください",
        )
        self.assertEqual(self.row("A-1").count(), 1)

    def test_update_conflict(self):
        # 修正画面を 2 つ開き、先の保存の後の保存は受け付けず、開き直しを求める
        context = self.start_shared_session()
        self.login(MANAGER[0], MANAGER[2])
        self.row("A-1").get_by_role("button", name="修正").click()
        other = context.new_page()
        other.goto(self.base + "/equipment/A-1/edit/")
        other.fill("#id_name", "先の名前")
        other.get_by_role("button", name="保存").click()
        other.wait_for_url(self.base + "/")
        self.page.fill("#id_name", "遅れた名前")
        self.page.get_by_role("button", name="保存").click()
        self.assertEqual(
            self.page.locator(".error").inner_text(),
            "他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください",
        )
        self.assertEqual(self.page.input_value("#id_name"), "遅れた名前")
        self.open("/")
        self.assertEqual(self.row("A-1").locator("td").nth(1).inner_text(), "先の名前")

    def test_update_keeps_lending(self):
        # 管理番号と備品名を変えても、貸出中・借りている社員・貸出日は同じ備品に残る
        seed_lending(self.data_dir, [("A-1", EMPLOYEE[0], "2026-01-15")])
        self.login(MANAGER[0], MANAGER[2])
        self.row("A-1").get_by_role("button", name="修正").click()
        self.page.fill("#id_equipment_number", "B-9")
        self.page.fill("#id_name", "新しい名前")
        self.page.get_by_role("button", name="保存").click()
        self.page.wait_for_url(self.base + "/")
        cells = self.row("B-9").locator("td").all_inner_texts()
        self.assertEqual(cells[:5], ["B-9", "新しい名前", "貸出中", EMPLOYEE[1], "2026-01-15"])
        self.assertEqual(self.row("A-1").count(), 0)
