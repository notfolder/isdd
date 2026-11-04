"""単体テストと結合テスト（入力検査、パスワード、セッション、業務ルール）。

実行: python3 -m unittest discover -s tests/unit
"""

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import accounts, equipment, lending, sessions, validation  # noqa: E402
from app.db import initialize_schema, open_connection  # noqa: E402
from app.security import hash_password, verify_password  # noqa: E402


class TestValidation(unittest.TestCase):
    def test_employee_number(self) -> None:
        self.assertIsNone(validation.validate_employee_number("123456"))
        for bad in ["12345", "1234567", "12345a", "１２３４５６", ""]:
            self.assertIsNotNone(validation.validate_employee_number(bad), bad)

    def test_name_boundaries(self) -> None:
        self.assertIsNone(validation.validate_name("あ" * 30))
        self.assertIsNotNone(validation.validate_name("あ" * 31))
        self.assertIsNotNone(validation.validate_name("   "))

    def test_password_minimum(self) -> None:
        self.assertIsNone(validation.validate_password("12345678"))
        self.assertIsNotNone(validation.validate_password("1234567"))

    def test_equipment_number(self) -> None:
        self.assertIsNone(validation.validate_equipment_number("A" * 20))
        self.assertIsNone(validation.validate_equipment_number("EQ-0001"))
        self.assertIsNotNone(validation.validate_equipment_number("A" * 21))
        self.assertIsNotNone(validation.validate_equipment_number("EQ 01"))
        self.assertIsNotNone(validation.validate_equipment_number("備品1"))

    def test_equipment_name(self) -> None:
        self.assertIsNone(validation.validate_equipment_name("名" * 50))
        self.assertIsNotNone(validation.validate_equipment_name("名" * 51))

    def test_lent_on(self) -> None:
        today = date(2026, 11, 4)
        self.assertIsNone(validation.validate_lent_on("2026-11-04", today))
        self.assertIsNone(validation.validate_lent_on("2026-01-01", today))
        self.assertIn("未来", validation.validate_lent_on("2026-11-05", today))
        self.assertIsNotNone(validation.validate_lent_on("2026-02-30", today))
        self.assertIsNotNone(validation.validate_lent_on("", today))


class TestSecurity(unittest.TestCase):
    def test_hash_and_verify(self) -> None:
        stored = hash_password("password1")
        self.assertNotIn("password1", stored)
        self.assertTrue(verify_password("password1", stored))
        self.assertFalse(verify_password("password2", stored))
        self.assertFalse(verify_password("password1", "broken"))


class DatabaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db_path = Path(self.tmp.name) / "test.sqlite3"
        initialize_schema(self.db_path)
        self.conn = open_connection(self.db_path)
        self.addCleanup(self.conn.close)


class TestSessions(DatabaseTestCase):
    def test_idle_timeout(self) -> None:
        accounts.register_account(self.conn, "123456", "山田", "password1")
        token = sessions.create_session(self.conn, "123456", now=1000)
        self.assertEqual(sessions.resolve_session(self.conn, token, 1800, now=2000)["employee_number"], "123456")
        self.assertIsNone(sessions.resolve_session(self.conn, token, 1800, now=2000 + 1801))

    def test_require_manager(self) -> None:
        self.assertEqual(sessions.require_manager(None), "login")
        self.assertEqual(sessions.require_manager({"role": "member"}), "forbidden")
        self.assertIsNone(sessions.require_manager({"role": "manager"}))


class TestAccountRules(DatabaseTestCase):
    def test_first_account_is_manager_and_limit(self) -> None:
        self.assertIsNone(accounts.register_account(self.conn, "000001", "一人目", "password1"))
        self.assertIsNone(accounts.register_account(self.conn, "000002", "二人目", "password1"))
        roles = {a["employee_number"]: a["role"] for a in accounts.list_accounts(self.conn)}
        self.assertEqual(roles, {"000001": "manager", "000002": "member"})

    def test_last_manager_cannot_be_removed(self) -> None:
        accounts.register_account(self.conn, "000001", "担当", "password1")
        problem = accounts.change_manager_role(self.conn, "000001", make_manager=False)
        self.assertEqual(problem[2], "担当者が 1 人もいなくなるため、この操作はできません")
        self.assertIsNotNone(accounts.delete_account(self.conn, "000001"))

    def test_borrowed_account_cannot_be_deleted(self) -> None:
        accounts.register_account(self.conn, "000001", "担当", "password1")
        accounts.register_account(self.conn, "000002", "社員", "password1")
        equipment.create_equipment(self.conn, "EQ-1", "備品")
        equipment_id = self.conn.execute("SELECT id FROM equipment").fetchone()["id"]
        self.assertIsNone(lending.lend_equipment(self.conn, equipment_id, "000002", "2026-01-01", date(2026, 11, 4)))
        problem = accounts.delete_account(self.conn, "000002")
        self.assertIn("備品を借りているため", problem[2])


class TestEquipmentRules(DatabaseTestCase):
    def test_version_conflict_and_lent_delete(self) -> None:
        equipment.create_equipment(self.conn, "EQ-1", "備品")
        row = self.conn.execute("SELECT id, version FROM equipment").fetchone()
        self.assertIsNone(equipment.update_equipment(self.conn, row["id"], row["version"], "EQ-1", "新名"))
        stale = equipment.update_equipment(self.conn, row["id"], row["version"], "EQ-2", "古い")
        self.assertEqual(stale[0], "error")
        self.assertIn("他の担当者が先に", stale[2])

    def test_duplicate_number(self) -> None:
        equipment.create_equipment(self.conn, "EQ-1", "備品")
        problem = equipment.create_equipment(self.conn, "EQ-1", "別")
        self.assertEqual(problem, ("field", "id_equipment_number", "この管理番号は既に使われています"))


if __name__ == "__main__":
    unittest.main()
