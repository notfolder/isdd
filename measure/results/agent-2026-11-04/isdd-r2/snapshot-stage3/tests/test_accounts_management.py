"""アカウントの管理（一覧、担当者の付け外し、パスワードの再設定、削除、要求ごとの同期）の単体・結合テスト（一時 DB）。"""

import os
import sys
import tempfile
import threading
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from equipment_ledger.core import validation  # noqa: E402
from equipment_ledger.core.accounts import (  # noqa: E402
    DELETE_LAST_MANAGER,
    DELETE_LENT,
    DELETE_NO_ACCOUNT,
    DELETE_OK,
    RESET_NO_ACCOUNT,
    RESET_OK,
    ROLE_CHANGE_OK,
    ROLE_LAST_MANAGER,
    ROLE_MANAGER,
    ROLE_MEMBER,
    ROLE_NO_ACCOUNT,
    authenticate,
    change_account_role,
    delete_account,
    list_accounts,
    list_borrower_candidates,
    register_account,
    reset_password,
)
from equipment_ledger.core.db import initialize_schema, open_connection  # noqa: E402
from equipment_ledger.core.equipment import register_equipment  # noqa: E402
from equipment_ledger.core.lending import LEND_NO_BORROWER, LEND_OK, lend_equipment  # noqa: E402


class _DbCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.conn = open_connection(self.tmp.name)
        initialize_schema(self.conn)
        register_account(self.conn, "111111", "担当A", "12345678")  # 担当者
        register_account(self.conn, "222222", "社員B", "12345678")  # 社員
        register_account(self.conn, "333333", "社員C", "12345678")  # 社員

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def role_of(self, number):
        row = self.conn.execute("SELECT role FROM account WHERE employee_number = ?", (number,)).fetchone()
        return row["role"] if row else None


class ListAccountsTest(_DbCase):
    def test_sorted_by_employee_number_without_hash(self):
        rows = list_accounts(self.conn)
        self.assertEqual([r["employee_number"] for r in rows], ["111111", "222222", "333333"])
        self.assertEqual(set(rows[0].keys()), {"employee_number", "name", "role"})
        self.assertEqual(rows[0]["role"], ROLE_MANAGER)
        self.assertEqual(rows[1]["role"], ROLE_MEMBER)


class ChangeRoleTest(_DbCase):
    def test_promote_then_demote_with_two_managers(self):
        self.assertEqual(change_account_role(self.conn, "222222", ROLE_MANAGER), ROLE_CHANGE_OK)
        self.assertEqual(self.role_of("222222"), ROLE_MANAGER)
        self.assertEqual(change_account_role(self.conn, "111111", ROLE_MEMBER), ROLE_CHANGE_OK)
        self.assertEqual(self.role_of("111111"), ROLE_MEMBER)

    def test_last_manager_cannot_be_demoted(self):
        self.assertEqual(change_account_role(self.conn, "111111", ROLE_MEMBER), ROLE_LAST_MANAGER)
        self.assertEqual(self.role_of("111111"), ROLE_MANAGER)

    def test_missing_account(self):
        self.assertEqual(change_account_role(self.conn, "999999", ROLE_MANAGER), ROLE_NO_ACCOUNT)

    def test_concurrent_demotion_keeps_one_manager(self):
        self.assertEqual(change_account_role(self.conn, "222222", ROLE_MANAGER), ROLE_CHANGE_OK)
        results = []
        barrier = threading.Barrier(2)

        def run(number):
            conn = open_connection(self.tmp.name)
            try:
                barrier.wait()
                results.append(change_account_role(conn, number, ROLE_MEMBER))
            finally:
                conn.close()

        threads = [threading.Thread(target=run, args=(n,)) for n in ("111111", "222222")]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(sorted(results), sorted([ROLE_CHANGE_OK, ROLE_LAST_MANAGER]))
        managers = [r for r in list_accounts(self.conn) if r["role"] == ROLE_MANAGER]
        self.assertEqual(len(managers), 1)


class ResetPasswordTest(_DbCase):
    def test_old_password_fails_after_reset(self):
        self.assertEqual(reset_password(self.conn, "222222", "87654321"), RESET_OK)
        self.assertIsNone(authenticate(self.conn, "222222", "12345678"))
        self.assertIsNotNone(authenticate(self.conn, "222222", "87654321"))

    def test_missing_account(self):
        self.assertEqual(reset_password(self.conn, "999999", "87654321"), RESET_NO_ACCOUNT)


class DeleteAccountTest(_DbCase):
    def test_delete_member_removes_candidate_and_login(self):
        self.assertEqual(delete_account(self.conn, "222222"), DELETE_OK)
        self.assertIsNone(authenticate(self.conn, "222222", "12345678"))
        numbers = [c["employee_number"] for c in list_borrower_candidates(self.conn)]
        self.assertNotIn("222222", numbers)

    def test_deny_when_lending_borrower(self):
        register_equipment(self.conn, "PC-0001", "ノートパソコン")
        self.assertEqual(lend_equipment(self.conn, "PC-0001", "222222", "2026-11-04"), LEND_OK)
        self.assertEqual(delete_account(self.conn, "222222"), DELETE_LENT)
        self.assertEqual(self.role_of("222222"), ROLE_MEMBER)

    def test_allowed_after_return(self):
        from equipment_ledger.core.lending import return_equipment

        register_equipment(self.conn, "PC-0001", "ノートパソコン")
        lend_equipment(self.conn, "PC-0001", "222222", "2026-11-04")
        return_equipment(self.conn, "PC-0001")
        self.assertEqual(delete_account(self.conn, "222222"), DELETE_OK)

    def test_deny_last_manager(self):
        self.assertEqual(delete_account(self.conn, "111111"), DELETE_LAST_MANAGER)
        self.assertEqual(self.role_of("111111"), ROLE_MANAGER)

    def test_delete_manager_when_two_managers(self):
        change_account_role(self.conn, "222222", ROLE_MANAGER)
        self.assertEqual(delete_account(self.conn, "111111"), DELETE_OK)

    def test_missing_account(self):
        self.assertEqual(delete_account(self.conn, "999999"), DELETE_NO_ACCOUNT)

    def test_lending_and_deletion_are_serialized(self):
        """貸出の登録と削除が同時に来ても、借りている社員が消えたまま貸出が残ることはない。"""
        register_equipment(self.conn, "PC-0001", "ノートパソコン")
        results = {}
        barrier = threading.Barrier(2)

        def lend():
            conn = open_connection(self.tmp.name)
            try:
                barrier.wait()
                results["lend"] = lend_equipment(conn, "PC-0001", "333333", "2026-11-04")
            finally:
                conn.close()

        def delete():
            conn = open_connection(self.tmp.name)
            try:
                barrier.wait()
                results["delete"] = delete_account(conn, "333333")
            finally:
                conn.close()

        threads = [threading.Thread(target=lend), threading.Thread(target=delete)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        lending = self.conn.execute("SELECT employee_number FROM lending").fetchall()
        if results["lend"] == LEND_OK:
            self.assertEqual(results["delete"], DELETE_LENT)
            self.assertEqual(len(lending), 1)
        else:
            self.assertEqual(results["lend"], LEND_NO_BORROWER)
            self.assertEqual(results["delete"], DELETE_OK)
            self.assertEqual(lending, [])


class PasswordValidationTest(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(validation.validate_password_input("1234567"), {"new_password": "パスワードは 8 文字以上で入力してください"})
        self.assertEqual(validation.validate_password_input("12345678"), {})
        self.assertIn("new_password", validation.validate_password_input(""))


class SessionSyncTest(unittest.TestCase):
    """要求ごとの同期（権限の変更と削除の反映）を、Flask のテストクライアントで確かめる。"""

    def setUp(self):
        from equipment_ledger.app import create_app

        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({"data_dir": self.tmp.name, "idle_timeout_seconds": 1800})
        self.app.config["TESTING"] = True
        self.conn = open_connection(self.tmp.name)
        register_account(self.conn, "111111", "担当A", "12345678")
        register_account(self.conn, "222222", "社員B", "12345678")
        self.client = self.app.test_client()

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def login(self, number):
        self.client.post("/login/", data={"employee_number": number, "password": "12345678"})

    def test_demoted_member_loses_manager_access(self):
        change_account_role(self.conn, "222222", ROLE_MANAGER)
        self.login("222222")
        self.assertEqual(self.client.get("/accounts/").status_code, 200)
        change_account_role(self.conn, "222222", ROLE_MEMBER)
        resp = self.client.get("/accounts/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/", resp.headers["Location"])

    def test_deleted_account_is_logged_out(self):
        self.login("222222")
        self.assertEqual(self.client.get("/").status_code, 200)
        delete_account(self.conn, "222222")
        resp = self.client.get("/accounts/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login/", resp.headers["Location"])


if __name__ == "__main__":
    unittest.main()
