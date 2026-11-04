"""入力検査の単体テスト。"""

import unittest

from src import validation as v


class AccountValidationTest(unittest.TestCase):
    def test_valid_input_has_no_errors(self):
        self.assertEqual(v.validate_account_input("000123", "山田太郎", "12345678"), {})

    def test_employee_number_must_be_six_digits(self):
        for bad in ["12345", "1234567", "12345a", "", "１２３４５６"]:
            errors = v.validate_account_input(bad, "名前", "12345678")
            self.assertEqual(errors["employee_number"], v.MSG_EMPLOYEE_NUMBER_FORMAT, bad)

    def test_name_required_and_max_30(self):
        self.assertEqual(v.validate_account_input("000001", "", "12345678")["name"], v.MSG_NAME_REQUIRED)
        self.assertEqual(v.validate_account_input("000001", "a" * 30, "12345678"), {})
        self.assertEqual(v.validate_account_input("000001", "a" * 31, "12345678")["name"], v.MSG_NAME_TOO_LONG)

    def test_password_min_8(self):
        self.assertEqual(v.validate_account_input("000001", "a", "1234567")["password"], v.MSG_PASSWORD_TOO_SHORT)
        self.assertEqual(v.validate_account_input("000001", "a", "12345678"), {})


class EquipmentValidationTest(unittest.TestCase):
    def test_valid_input_has_no_errors(self):
        self.assertEqual(v.validate_equipment_input("PC-0001", "ノートパソコン"), {})

    def test_number_format(self):
        for bad in ["", "PC_1", "日本語", "A" * 21, "PC 1"]:
            self.assertEqual(
                v.validate_equipment_input(bad, "x")["equipment_number"], v.MSG_EQUIPMENT_NUMBER_FORMAT, bad
            )
        self.assertEqual(v.validate_equipment_input("A" * 20, "x"), {})

    def test_name_required_and_max_50(self):
        self.assertEqual(v.validate_equipment_input("A-1", "")["name"], v.MSG_EQUIPMENT_NAME_REQUIRED)
        self.assertEqual(v.validate_equipment_input("A-1", "a" * 50), {})
        self.assertEqual(v.validate_equipment_input("A-1", "a" * 51)["name"], v.MSG_EQUIPMENT_NAME_TOO_LONG)
