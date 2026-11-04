"""アカウント登録とログイン照合の単体テスト。"""

import unittest

from src import accounts, db
from tests.helpers import make_data_dir


class AccountsTest(unittest.TestCase):
    def setUp(self):
        self.data_dir = make_data_dir()
        self.conn = db.connect(self.data_dir)

    def tearDown(self):
        self.conn.close()

    def test_first_account_is_manager_second_is_employee(self):
        errors, role = accounts.register_account(self.conn, "000001", "担当", "password1")
        self.assertEqual(errors, {})
        self.assertEqual(role, accounts.ROLE_MANAGER)
        errors, role = accounts.register_account(self.conn, "000002", "社員", "password2")
        self.assertEqual(errors, {})
        self.assertEqual(role, accounts.ROLE_EMPLOYEE)

    def test_duplicate_employee_number_is_rejected(self):
        accounts.register_account(self.conn, "000001", "担当", "password1")
        errors, role = accounts.register_account(self.conn, "000001", "別", "password2")
        self.assertEqual(errors, {"employee_number": accounts.MSG_EMPLOYEE_NUMBER_DUPLICATE})
        self.assertIsNone(role)

    def test_password_is_hashed_not_stored_plain(self):
        accounts.register_account(self.conn, "000001", "担当", "password1")
        row = self.conn.execute("SELECT password_hash FROM accounts").fetchone()
        self.assertNotIn("password1", row["password_hash"])

    def test_verify_login(self):
        accounts.register_account(self.conn, "000001", "担当", "password1")
        self.assertTrue(accounts.verify_login(self.conn, "000001", "password1"))
        self.assertFalse(accounts.verify_login(self.conn, "000001", "wrong-pass"))
        self.assertFalse(accounts.verify_login(self.conn, "999999", "password1"))

    def test_hash_is_salted(self):
        self.assertNotEqual(accounts.hash_password("same-pass"), accounts.hash_password("same-pass"))
