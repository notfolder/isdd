"""備品の一覧・登録・修正・削除の単体テスト。"""

import unittest

from src import db, equipment, lending
from tests.helpers import make_data_dir


def seed_account(conn, number="0000001"):
    """借りる社員の候補になるアカウントを 1 件作る（直接の挿入。ハッシュの計算は省く）。"""
    conn.execute(
        "INSERT INTO accounts (employee_number, name, password_hash, role, created_at) "
        "VALUES (?, '社員', 'x', 'employee', '2026-11-05T00:00:00+00:00')",
        (number,),
    )


class EquipmentTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(make_data_dir())

    def tearDown(self):
        self.conn.close()

    def updated_at(self, number):
        return equipment.get_equipment(self.conn, number)["updated_at"]

    def test_list_is_sorted_by_number(self):
        equipment.create_equipment(self.conn, "B-2", "b")
        equipment.create_equipment(self.conn, "A-10", "a")
        numbers = [row["equipment_number"] for row in equipment.list_equipment(self.conn)]
        self.assertEqual(numbers, ["A-10", "B-2"])

    def test_list_shows_lending_when_lent(self):
        seed_account(self.conn)
        equipment.create_equipment(self.conn, "A-1", "a")
        equipment.create_equipment(self.conn, "A-2", "b")
        lending.lend_equipment(self.conn, "A-2", "0000001", "2026-11-05")
        rows = {row["equipment_number"]: row for row in equipment.list_equipment(self.conn)}
        self.assertFalse(rows["A-1"]["lent"])
        self.assertIsNone(rows["A-1"]["borrower_name"])
        self.assertTrue(rows["A-2"]["lent"])
        self.assertEqual(rows["A-2"]["borrower_name"], "社員")
        self.assertEqual(rows["A-2"]["lent_on"], "2026-11-05")

    def test_duplicate_number_on_create_is_rejected(self):
        equipment.create_equipment(self.conn, "A-1", "a")
        errors, status = equipment.create_equipment(self.conn, "A-1", "dup")
        self.assertEqual(errors, {"equipment_number": equipment.MSG_EQUIPMENT_NUMBER_DUPLICATE})
        self.assertEqual(status, equipment.STATUS_INVALID)
        self.assertEqual(len(equipment.list_equipment(self.conn)), 1)

    def test_number_is_case_sensitive(self):
        equipment.create_equipment(self.conn, "A-1", "a")
        errors, _ = equipment.create_equipment(self.conn, "a-1", "b")
        self.assertEqual(errors, {})

    def test_update_to_own_number_is_not_duplicate(self):
        equipment.create_equipment(self.conn, "A-1", "a")
        errors, status = equipment.update_equipment(
            self.conn, "A-1", "A-1", "新しい名前", self.updated_at("A-1")
        )
        self.assertEqual((errors, status), ({}, equipment.STATUS_OK))
        self.assertEqual(equipment.get_equipment(self.conn, "A-1")["name"], "新しい名前")

    def test_update_to_taken_number_is_rejected(self):
        equipment.create_equipment(self.conn, "A-1", "a")
        equipment.create_equipment(self.conn, "A-2", "b")
        errors, status = equipment.update_equipment(
            self.conn, "A-1", "A-2", "x", self.updated_at("A-1")
        )
        self.assertIn("equipment_number", errors)
        self.assertEqual(status, equipment.STATUS_INVALID)
        self.assertEqual(equipment.get_equipment(self.conn, "A-1")["name"], "a")

    def test_update_with_stale_token_is_conflict(self):
        equipment.create_equipment(self.conn, "A-1", "a")
        stale = self.updated_at("A-1")
        equipment.update_equipment(self.conn, "A-1", "A-1", "他の人の変更", stale)
        errors, status = equipment.update_equipment(self.conn, "A-1", "A-1", "遅れた変更", stale)
        self.assertEqual((errors, status), ({}, equipment.STATUS_CONFLICT))
        self.assertEqual(equipment.get_equipment(self.conn, "A-1")["name"], "他の人の変更")

    def test_update_of_deleted_equipment_is_conflict(self):
        equipment.create_equipment(self.conn, "A-1", "a")
        token = self.updated_at("A-1")
        equipment.delete_equipment(self.conn, "A-1")
        _, status = equipment.update_equipment(self.conn, "A-1", "A-1", "x", token)
        self.assertEqual(status, equipment.STATUS_CONFLICT)

    def test_update_keeps_lending_when_number_changes(self):
        seed_account(self.conn)
        equipment.create_equipment(self.conn, "A-1", "a")
        lending.lend_equipment(self.conn, "A-1", "0000001", "2026-11-05")
        _, status = equipment.update_equipment(
            self.conn, "A-1", "B-9", "新しい名前", self.updated_at("A-1")
        )
        self.assertEqual(status, equipment.STATUS_OK)
        rows = equipment.list_equipment(self.conn)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["equipment_number"], "B-9")
        self.assertTrue(rows[0]["lent"])
        self.assertEqual(rows[0]["borrower_name"], "社員")
        self.assertEqual(rows[0]["lent_on"], "2026-11-05")

    def test_update_missing_is_conflict(self):
        _, status = equipment.update_equipment(self.conn, "NONE", "NONE", "x", "t")
        self.assertEqual(status, equipment.STATUS_CONFLICT)

    def test_delete_and_delete_missing(self):
        equipment.create_equipment(self.conn, "A-1", "a")
        self.assertEqual(equipment.delete_equipment(self.conn, "A-1"), equipment.STATUS_OK)
        self.assertEqual(equipment.delete_equipment(self.conn, "A-1"), equipment.STATUS_NOT_FOUND)
        self.assertEqual(equipment.list_equipment(self.conn), [])

    def test_delete_lent_equipment_is_refused(self):
        seed_account(self.conn)
        equipment.create_equipment(self.conn, "A-1", "a")
        lending.lend_equipment(self.conn, "A-1", "0000001", "2026-11-05")
        self.assertEqual(equipment.delete_equipment(self.conn, "A-1"), equipment.STATUS_LENT)
        self.assertEqual(len(equipment.list_equipment(self.conn)), 1)
        lending.return_equipment(self.conn, "A-1")
        self.assertEqual(equipment.delete_equipment(self.conn, "A-1"), equipment.STATUS_OK)


if __name__ == "__main__":
    unittest.main()
