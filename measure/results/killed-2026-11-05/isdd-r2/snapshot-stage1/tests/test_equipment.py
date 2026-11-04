"""備品の一覧・登録・修正・削除の単体テスト。"""

import unittest

from src import db, equipment
from tests.helpers import make_data_dir


class EquipmentTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(make_data_dir())

    def tearDown(self):
        self.conn.close()

    def test_list_is_sorted_by_number(self):
        equipment.create_equipment(self.conn, "B-2", "b")
        equipment.create_equipment(self.conn, "A-10", "a")
        numbers = [row["equipment_number"] for row in equipment.list_equipment(self.conn)]
        self.assertEqual(numbers, ["A-10", "B-2"])

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
        errors, status = equipment.update_equipment(self.conn, "A-1", "A-1", "新しい名前")
        self.assertEqual((errors, status), ({}, equipment.STATUS_OK))
        self.assertEqual(equipment.get_equipment(self.conn, "A-1")["name"], "新しい名前")

    def test_update_to_taken_number_is_rejected(self):
        equipment.create_equipment(self.conn, "A-1", "a")
        equipment.create_equipment(self.conn, "A-2", "b")
        errors, status = equipment.update_equipment(self.conn, "A-1", "A-2", "x")
        self.assertIn("equipment_number", errors)
        self.assertEqual(status, equipment.STATUS_INVALID)
        self.assertEqual(equipment.get_equipment(self.conn, "A-1")["name"], "a")

    def test_update_missing_is_not_found(self):
        _, status = equipment.update_equipment(self.conn, "NONE", "NONE", "x")
        self.assertEqual(status, equipment.STATUS_NOT_FOUND)

    def test_delete_and_delete_missing(self):
        equipment.create_equipment(self.conn, "A-1", "a")
        self.assertEqual(equipment.delete_equipment(self.conn, "A-1"), equipment.STATUS_OK)
        self.assertEqual(equipment.delete_equipment(self.conn, "A-1"), equipment.STATUS_NOT_FOUND)
        self.assertEqual(equipment.list_equipment(self.conn), [])
