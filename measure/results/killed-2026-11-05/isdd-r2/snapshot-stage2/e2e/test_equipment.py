"""備品の台帳と貸出状況の E2E テスト。実行: 詳細設計書 8-4 のコマンド。"""

import time

from e2e.support import LedgerE2ECase, seed_accounts, seed_equipment
from src import accounts, db

MANAGER = ("0000001", "担当", "password1")
EMPLOYEE = ("0000002", "社員", "password2")


class RegisterEquipmentE2E(LedgerE2ECase):
    """担当者による備品の登録。"""

    def prepare_data(self):
        seed_accounts(self.data_dir, [MANAGER])

    def test_register_equipment(self):
        # 担当者が登録すると「空き」で一覧に出る
        self.login(MANAGER[0], MANAGER[2])
        self.page.get_by_role("link", name="備品を登録").click()
        self.page.fill("#id_equipment_number", "PC-0001")
        self.page.fill("#id_name", "ノートパソコン")
        self.page.get_by_role("button", name="保存").click()
        self.page.wait_for_url(self.base + "/")
        cells = self.row("PC-0001").locator("td").all_inner_texts()
        self.assertEqual(cells[:3], ["PC-0001", "ノートパソコン", "空き"])

    def test_equipment_input_validation(self):
        # 形式、重複、長さの検査
        seed_equipment(self.data_dir, [("A-1", "既存")])
        self.login(MANAGER[0], MANAGER[2])
        self.open("/equipment/new/")
        self.page.fill("#id_equipment_number", "A_1")
        self.page.fill("#id_name", "x")
        self.page.get_by_role("button", name="保存").click()
        self.assertEqual(
            self.page.locator(".field .field-error").inner_text(),
            "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください",
        )
        self.assertEqual(self.page.input_value("#id_equipment_number"), "A_1")
        self.page.fill("#id_equipment_number", "A-1")
        self.page.get_by_role("button", name="保存").click()
        self.assertEqual(
            self.page.locator(".field .field-error").inner_text(), "この管理番号は既に使われています"
        )
        self.page.fill("#id_equipment_number", "B-1")
        self.page.fill("#id_name", "a" * 51)
        self.page.get_by_role("button", name="保存").click()
        self.assertEqual(
            self.page.locator(".field .field-error").inner_text(), "備品名は 50 文字以内で入力してください"
        )
        self.assertEqual(self.page.locator("tbody tr").count(), 0)
        self.open("/")
        self.assertEqual(self.page.locator("tbody tr").count(), 1)


class ManageEquipmentE2E(LedgerE2ECase):
    """担当者による修正と削除。"""

    def prepare_data(self):
        seed_accounts(self.data_dir, [MANAGER])
        seed_equipment(self.data_dir, [("A-1", "旧い名前")])

    def test_update_equipment(self):
        # 行の「修正」から備品名を変えて保存する
        self.login(MANAGER[0], MANAGER[2])
        self.row("A-1").get_by_role("button", name="修正").click()
        self.page.fill("#id_name", "新しい名前")
        self.page.get_by_role("button", name="保存").click()
        self.page.wait_for_url(self.base + "/")
        self.assertEqual(self.row("A-1").locator("td").nth(1).inner_text(), "新しい名前")

    def test_delete_equipment_needs_confirmation(self):
        # 確認でキャンセルすると残り、「はい」で消える
        self.login(MANAGER[0], MANAGER[2])
        self.page.once("dialog", lambda dialog: dialog.dismiss())
        self.row("A-1").get_by_role("button", name="削除").click()
        self.page.wait_for_timeout(300)
        self.assertEqual(self.row("A-1").count(), 1)
        self.page.once("dialog", lambda dialog: dialog.accept())
        self.row("A-1").get_by_role("button", name="削除").click()
        self.page.wait_for_selector("tbody tr", state="detached", timeout=5000)
        self.assertEqual(self.page.locator("tbody tr").count(), 0)


class ViewEquipmentE2E(LedgerE2ECase):
    """誰でも見られる貸出状況。"""

    def test_view_status_anonymous(self):
        # 未ログインでも昇順で見え、ボタンは出ない
        seed_equipment(self.data_dir, [("B-2", "二番"), ("A-10", "一番")])
        self.open("/")
        numbers = self.page.locator("tbody tr").evaluate_all(
            "rows => rows.map(r => r.dataset.equipmentNumber)"
        )
        self.assertEqual(numbers, ["A-10", "B-2"])
        cells = self.row("A-10").locator("td").all_inner_texts()
        self.assertEqual(cells, ["A-10", "一番", "空き", "", ""])
        self.assertEqual(self.page.get_by_role("button").count(), 0)

    def test_view_status_empty(self):
        # 0 件なら案内を出し、表は出さない
        self.open("/")
        self.assertEqual(self.page.locator(".empty").inner_text(), "備品は登録されていません")
        self.assertEqual(self.page.locator("table").count(), 0)


class PermissionE2E(LedgerE2ECase):
    """社員と未ログインの人による操作の拒否。"""

    def prepare_data(self):
        seed_accounts(self.data_dir, [MANAGER, EMPLOYEE])
        seed_equipment(self.data_dir, [("A-1", "残す")])

    def test_employee_cannot_operate(self):
        # 社員はボタンが無く、直接の要求も拒否される
        self.login(EMPLOYEE[0], EMPLOYEE[2])
        self.assertEqual(self.page.get_by_role("button", name="修正").count(), 0)
        self.assertEqual(self.page.get_by_role("button", name="削除").count(), 0)
        self.open("/equipment/new/")
        self.assertEqual(self.page.url, self.base + "/?notice=manager_only")
        self.assertEqual(self.page.locator(".message").inner_text(), "この操作は担当者だけが行えます")
        response = self.page.request.post(self.base + "/equipment/A-1/delete/", max_redirects=0)
        self.assertEqual(response.status, 302)
        self.open("/")
        self.assertEqual(self.row("A-1").count(), 1)

    def test_anonymous_cannot_operate(self):
        # 未ログインは登録画面に入れず、要求もログイン画面へ転送される
        self.open("/equipment/new/")
        self.assertIn("/login/", self.page.url)
        response = self.page.request.post(self.base + "/equipment/A-1/delete/", max_redirects=0)
        self.assertEqual(response.status, 302)
        self.assertIn("/login/", response.headers["location"])
        self.open("/")
        self.assertEqual(self.row("A-1").count(), 1)


class NonFunctionalLoadE2E(LedgerE2ECase):
    """利用人数 50 人と備品 300 件（うち 100 件は貸出中）の規模で、一覧の表示が 3 秒以内であることを確かめる。"""

    def prepare_data(self):
        conn = db.connect(self.data_dir)
        try:
            accounts.register_account(conn, "0000001", "担当", "password1")
            # 50 人分のアカウント。ハッシュは 1 件目の値を共用する（規模の確認が目的のため）
            password_hash = conn.execute("SELECT password_hash FROM accounts").fetchone()[0]
            for index in range(2, 51):
                conn.execute(
                    "INSERT INTO accounts (employee_number, name, password_hash, role, created_at) "
                    "VALUES (?, ?, ?, 'employee', '2026-11-05T00:00:00+00:00')",
                    (f"{index:07d}", f"社員{index}", password_hash),
                )
            for index in range(1, 301):
                conn.execute(
                    "INSERT INTO equipment (equipment_number, name, created_at, updated_at) "
                    "VALUES (?, ?, '2026-11-05T00:00:00+00:00', '2026-11-05T00:00:00+00:00')",
                    (f"EQ-{index:04d}", f"備品{index}"),
                )
            # 100 件は貸出中にして、貸出の表の結合を含めて確かめる
            for index in range(1, 101):
                conn.execute(
                    "INSERT INTO lendings (equipment_number, employee_number, lent_on) VALUES (?, ?, '2026-11-05')",
                    (f"EQ-{index:04d}", f"{(index % 49) + 2:07d}"),
                )
        finally:
            conn.close()

    def test_status_page_responds_within_three_seconds(self):
        # 300 件（貸出中の 100 件を含む）の一覧の表示が 3 秒以内
        started = time.perf_counter()
        self.open("/")
        self.page.wait_for_selector("tbody tr[data-equipment-number='EQ-0300']")
        elapsed = time.perf_counter() - started
        self.assertEqual(self.page.locator("tbody tr").count(), 300)
        self.assertLess(elapsed, 3.0, f"表示に {elapsed:.2f} 秒かかった")
