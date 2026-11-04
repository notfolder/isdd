"""業務の関数の単体テスト。一時 DB を使い、Web の枠組みは使わない。"""

import datetime
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from app import accounts, equipment, loans, validation  # noqa: E402
from app.config import load_config  # noqa: E402
from app.db import connect, init_schema  # noqa: E402


class ConfigTest(unittest.TestCase):
    def test_defaults(self):
        config = load_config({})
        self.assertEqual(config["port"], 8000)
        self.assertEqual(config["idle_timeout_seconds"], 1800)
        self.assertEqual(config["data_dir"].name, "data")

    def test_values(self):
        config = load_config({"PORT": "9001", "DATA_DIR": "/tmp/x", "SESSION_IDLE_TIMEOUT_SECONDS": "60"})
        self.assertEqual((config["port"], config["idle_timeout_seconds"]), (9001, 60))

    def test_invalid_values(self):
        for bad in ({"PORT": "abc"}, {"PORT": "0"}, {"SESSION_IDLE_TIMEOUT_SECONDS": "-1"}):
            with self.assertRaises(ValueError):
                load_config(bad)


class ValidationTest(unittest.TestCase):
    def test_employee_number_boundaries(self):
        self.assertEqual(validation.validate_account_input("123456", "a", "12345678"), {})
        self.assertIn("employee_number", validation.validate_account_input("12345", "a", "12345678"))
        self.assertIn("employee_number", validation.validate_account_input("1234567", "a", "12345678"))
        self.assertIn("employee_number", validation.validate_account_input("１２３４５６", "a", "12345678"))

    def test_name_and_password_boundaries(self):
        self.assertEqual(validation.validate_account_input("000001", "a" * 30, "12345678"), {})
        self.assertIn("name", validation.validate_account_input("000001", "a" * 31, "12345678"))
        self.assertIn("name", validation.validate_account_input("000001", "  ", "12345678"))
        self.assertIn("password", validation.validate_account_input("000001", "a", "1234567"))

    def test_equipment_boundaries(self):
        self.assertEqual(validation.validate_equipment_input("A" * 20, "x" * 50), {})
        self.assertIn("equipment_number", validation.validate_equipment_input("A" * 21, "x"))
        self.assertIn("equipment_number", validation.validate_equipment_input("PC-01_2", "x"))
        self.assertIn("name", validation.validate_equipment_input("PC-1", "x" * 51))
        self.assertIn("name", validation.validate_equipment_input("PC-1", ""))


class DatabaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "unit.db"
        init_schema(self.db_path)
        self.conn = connect(self.db_path)

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def test_first_account_is_manager_and_second_is_member(self):
        self.assertEqual(accounts.register_account(self.conn, "000001", "山田", "password1"), {})
        self.assertEqual(accounts.register_account(self.conn, "000002", "佐藤", "password1"), {})
        first = accounts.authenticate_account(self.conn, "000001", "password1")
        second = accounts.authenticate_account(self.conn, "000002", "password1")
        self.assertEqual(first["role"], accounts.ROLE_MANAGER)
        self.assertEqual(second["role"], accounts.ROLE_MEMBER)

    def test_duplicate_employee_number_is_rejected(self):
        accounts.register_account(self.conn, "000001", "山田", "password1")
        errors = accounts.register_account(self.conn, "000001", "別人", "password1")
        self.assertEqual(errors, {"employee_number": "この社員番号は既に登録されています"})

    def test_authenticate_failure_returns_none(self):
        accounts.register_account(self.conn, "000001", "山田", "password1")
        self.assertIsNone(accounts.authenticate_account(self.conn, "000001", "wrong-one"))
        self.assertIsNone(accounts.authenticate_account(self.conn, "999999", "password1"))

    def test_equipment_crud(self):
        self.assertEqual(equipment.create_equipment(self.conn, "PC-2", "B"), {})
        self.assertEqual(equipment.create_equipment(self.conn, "PC-1", "A"), {})
        self.assertEqual(
            [r["equipment_number"] for r in loans.list_loan_status(self.conn)], ["PC-1", "PC-2"]
        )
        self.assertEqual(
            equipment.create_equipment(self.conn, "PC-1", "dup"),
            {"equipment_number": "この管理番号は既に使われています"},
        )
        current = equipment.get_equipment_with_revision(self.conn, "PC-1")
        self.assertEqual(current["revision"], 1)
        self.assertEqual(
            equipment.update_equipment_if_current(self.conn, "PC-1", 1, "PC-1", "A2"), {}
        )
        self.assertEqual(equipment.get_equipment_with_revision(self.conn, "PC-1")["revision"], 2)
        self.assertEqual(
            equipment.update_equipment_if_current(self.conn, "PC-1", 2, "PC-2", "x"),
            {"equipment_number": "この管理番号は既に使われています"},
        )
        self.assertEqual(
            equipment.delete_equipment_if_not_loaned(self.conn, "PC-1"), equipment.DELETE_DELETED
        )
        self.assertEqual(
            equipment.delete_equipment_if_not_loaned(self.conn, "PC-1"), equipment.DELETE_NOT_FOUND
        )
        self.assertIsNone(equipment.get_equipment_with_revision(self.conn, "PC-1"))

    def test_stale_revision_is_rejected(self):
        equipment.create_equipment(self.conn, "PC-1", "A")
        self.assertEqual(equipment.update_equipment_if_current(self.conn, "PC-1", 1, "PC-1", "B"), {})
        stale = equipment.update_equipment_if_current(self.conn, "PC-1", 1, "PC-1", "C")
        self.assertIn(equipment.CONFLICT_KEY, stale)
        self.assertEqual(equipment.get_equipment_with_revision(self.conn, "PC-1")["name"], "B")

    def test_loan_register_return_and_status(self):
        accounts.register_account(self.conn, "000001", "山田", "password1")
        accounts.register_account(self.conn, "000002", "佐藤", "password1")
        borrower = accounts.authenticate_account(self.conn, "000002", "password1")
        equipment.create_equipment(self.conn, "PC-1", "A")
        equipment.create_equipment(self.conn, "PC-2", "B")
        self.assertEqual(loans.register_loan(self.conn, "PC-1", borrower["id"], "2026-11-04"), loans.RESULT_OK)
        self.assertEqual(loans.register_loan(self.conn, "PC-1", borrower["id"], "2026-11-04"), loans.RESULT_LOANED)
        self.assertEqual(loans.register_loan(self.conn, "NONE", borrower["id"], "2026-11-04"), loans.RESULT_NOT_FOUND)
        self.assertEqual(loans.register_loan(self.conn, "PC-2", 9999, "2026-11-04"), loans.RESULT_NO_BORROWER)
        status = {r["equipment_number"]: r for r in loans.list_loan_status(self.conn)}
        self.assertTrue(status["PC-1"]["loaned"])
        self.assertEqual(status["PC-1"]["borrower_name"], "佐藤")
        self.assertEqual(status["PC-1"]["lent_on"], "2026-11-04")
        self.assertFalse(status["PC-2"]["loaned"])
        self.assertEqual(
            equipment.delete_equipment_if_not_loaned(self.conn, "PC-1"), equipment.DELETE_LOANED
        )
        self.assertEqual(loans.return_loan(self.conn, "PC-1"), loans.RESULT_OK)
        self.assertEqual(loans.return_loan(self.conn, "PC-1"), loans.RESULT_NOT_LOANED)
        self.assertEqual(loans.return_loan(self.conn, "NONE"), loans.RESULT_NOT_FOUND)
        self.assertFalse(loans.list_loan_status(self.conn)[0]["loaned"])

    def test_edit_keeps_loan(self):
        accounts.register_account(self.conn, "000001", "山田", "password1")
        manager = accounts.authenticate_account(self.conn, "000001", "password1")
        equipment.create_equipment(self.conn, "PC-1", "A")
        loans.register_loan(self.conn, "PC-1", manager["id"], "2026-11-01")
        self.assertEqual(
            equipment.update_equipment_if_current(self.conn, "PC-1", 1, "PC-9", "Z"), {}
        )
        row = loans.list_loan_status(self.conn)[0]
        self.assertEqual((row["equipment_number"], row["loaned"], row["borrower_name"]), ("PC-9", True, "山田"))
        self.assertEqual(row["lent_on"], "2026-11-01")

    def test_loan_input_boundaries(self):
        today = datetime.date(2026, 11, 4)
        self.assertEqual(validation.validate_loan_input("1", "2026-11-04", today), {})
        self.assertEqual(validation.validate_loan_input("1", "2026-01-01", today), {})
        self.assertIn("lent_on", validation.validate_loan_input("1", "2026-11-05", today))
        self.assertIn("lent_on", validation.validate_loan_input("1", "2026/11/04", today))
        self.assertIn("borrower", validation.validate_loan_input("", "2026-11-04", today))


if __name__ == "__main__":
    unittest.main()
