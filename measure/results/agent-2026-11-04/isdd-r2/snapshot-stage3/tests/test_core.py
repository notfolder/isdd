"""業務ロジック（core）と設定の単体テスト、結合テスト（一時 DB）。"""

import os
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from equipment_ledger.core import validation  # noqa: E402
from equipment_ledger.core.accounts import ROLE_MANAGER, ROLE_MEMBER, authenticate, register_account  # noqa: E402
from equipment_ledger.core.config import load_settings  # noqa: E402
from equipment_ledger.core.db import initialize_schema, open_connection  # noqa: E402
from equipment_ledger.core.equipment import (  # noqa: E402
    DELETE_MISSING,
    DELETE_OK,
    delete_equipment,
    get_equipment,
    list_equipment_status,
    register_equipment,
    update_equipment,
)


class ValidationTest(unittest.TestCase):
    def test_account_employee_number_format(self):
        self.assertEqual(validation.validate_account_input("123456", "a", "12345678"), {})
        for bad in ["12345", "1234567", "12345a", ""]:
            errors = validation.validate_account_input(bad, "a", "12345678")
            self.assertEqual(errors["employee_number"], validation.MSG_EMPLOYEE_NUMBER_FORMAT)

    def test_account_name_bounds(self):
        self.assertEqual(validation.validate_account_input("123456", "x" * 30, "12345678"), {})
        errors = validation.validate_account_input("123456", "x" * 31, "12345678")
        self.assertEqual(errors["name"], validation.MSG_NAME_TOO_LONG)
        errors = validation.validate_account_input("123456", "   ", "12345678")
        self.assertEqual(errors["name"], validation.MSG_NAME_REQUIRED)

    def test_account_password_bounds(self):
        self.assertEqual(validation.validate_account_input("123456", "a", "12345678"), {})
        errors = validation.validate_account_input("123456", "a", "1234567")
        self.assertEqual(errors["password"], validation.MSG_PASSWORD_TOO_SHORT)

    def test_equipment_number_bounds(self):
        self.assertEqual(validation.validate_equipment_input("A" * 20, "n"), {})
        self.assertEqual(validation.validate_equipment_input("PC-0001", "n"), {})
        for bad in ["A" * 21, "PC 0001", "備品1", ""]:
            errors = validation.validate_equipment_input(bad, "n")
            self.assertEqual(errors["equipment_number"], validation.MSG_EQUIPMENT_NUMBER_FORMAT)

    def test_equipment_name_bounds(self):
        self.assertEqual(validation.validate_equipment_input("PC-1", "n" * 50), {})
        errors = validation.validate_equipment_input("PC-1", "n" * 51)
        self.assertEqual(errors["name"], validation.MSG_EQUIPMENT_NAME_TOO_LONG)

    def test_edit_skips_number_check(self):
        self.assertEqual(validation.validate_equipment_input(None, "n"), {})


class ConfigTest(unittest.TestCase):
    def test_defaults_and_overrides(self):
        keys = ["PORT", "HOST", "DATA_DIR", "SESSION_IDLE_TIMEOUT_SECONDS"]
        saved = {k: os.environ.pop(k, None) for k in keys}
        try:
            s = load_settings()
            self.assertEqual((s["port"], s["host"], s["idle_timeout_seconds"]), (8000, "0.0.0.0", 1800))
            os.environ["PORT"] = "9001"
            os.environ["SESSION_IDLE_TIMEOUT_SECONDS"] = "2"
            s = load_settings()
            self.assertEqual((s["port"], s["idle_timeout_seconds"]), (9001, 2))
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


class CoreDbTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.conn = open_connection(self.tmp.name)
        initialize_schema(self.conn)
        initialize_schema(self.conn)  # 二重に作っても無害

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def test_first_account_is_manager_then_member(self):
        self.assertEqual(register_account(self.conn, "111111", "A", "12345678"), ROLE_MANAGER)
        self.assertEqual(register_account(self.conn, "222222", "B", "12345678"), ROLE_MEMBER)

    def test_duplicate_employee_number(self):
        register_account(self.conn, "111111", "A", "12345678")
        self.assertIsNone(register_account(self.conn, "111111", "X", "12345678"))

    def test_authenticate_same_result_for_both_mismatches(self):
        register_account(self.conn, "111111", "A", "12345678")
        self.assertEqual(authenticate(self.conn, "111111", "12345678")["role"], ROLE_MANAGER)
        self.assertIsNone(authenticate(self.conn, "111111", "wrong-password"))
        self.assertIsNone(authenticate(self.conn, "999999", "12345678"))

    def test_equipment_crud_and_order(self):
        self.assertEqual(list_equipment_status(self.conn), [])
        self.assertTrue(register_equipment(self.conn, "PC-0002", "B"))
        self.assertTrue(register_equipment(self.conn, "PC-0001", "A"))
        self.assertFalse(register_equipment(self.conn, "PC-0001", "dup"))
        numbers = [r["number"] for r in list_equipment_status(self.conn)]
        self.assertEqual(numbers, ["PC-0001", "PC-0002"])
        self.assertEqual(list_equipment_status(self.conn)[0]["status"], "空き")
        revision = get_equipment(self.conn, "PC-0001")["revision"]
        self.assertTrue(update_equipment(self.conn, "PC-0001", "A2", revision))
        self.assertEqual(get_equipment(self.conn, "PC-0001")["name"], "A2")
        self.assertFalse(update_equipment(self.conn, "PC-0001", "A3", revision))
        self.assertEqual(delete_equipment(self.conn, "PC-0001"), DELETE_OK)
        self.assertEqual(delete_equipment(self.conn, "PC-0001"), DELETE_MISSING)
        self.assertIsNone(get_equipment(self.conn, "PC-0001"))


if __name__ == "__main__":
    unittest.main()
