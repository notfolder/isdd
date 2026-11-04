"""業務の関数の単体テスト。一時 DB を使い、Web の枠組みは使わない。"""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from app import accounts, equipment, validation  # noqa: E402
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
            [r["equipment_number"] for r in equipment.list_equipment(self.conn)], ["PC-1", "PC-2"]
        )
        self.assertEqual(
            equipment.create_equipment(self.conn, "PC-1", "dup"),
            {"equipment_number": "この管理番号は既に使われています"},
        )
        self.assertEqual(equipment.update_equipment(self.conn, "PC-1", "PC-1", "A2"), {})
        self.assertEqual(equipment.get_equipment(self.conn, "PC-1")["name"], "A2")
        self.assertEqual(
            equipment.update_equipment(self.conn, "PC-1", "PC-2", "x"),
            {"equipment_number": "この管理番号は既に使われています"},
        )
        self.assertTrue(equipment.delete_equipment(self.conn, "PC-1"))
        self.assertFalse(equipment.delete_equipment(self.conn, "PC-1"))
        self.assertIsNone(equipment.get_equipment(self.conn, "PC-1"))


if __name__ == "__main__":
    unittest.main()
