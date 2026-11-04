"""入力検査の単体テスト。"""

import unittest
from datetime import date

from src import validation as v


class AccountValidationTest(unittest.TestCase):
    def test_valid_input_has_no_errors(self):
        self.assertEqual(v.validate_account_input("0000123", "山田太郎", "12345678"), {})
        self.assertEqual(v.validate_account_input("0000000", "山田太郎", "12345678"), {})

    def test_employee_number_must_be_seven_digits(self):
        for bad in ["123456", "12345678", "12345a", "", "１２３４５６７"]:
            errors = v.validate_account_input(bad, "名前", "12345678")
            self.assertEqual(errors["employee_number"], v.MSG_EMPLOYEE_NUMBER_FORMAT, bad)

    def test_name_required_and_max_30(self):
        self.assertEqual(v.validate_account_input("0000001", "", "12345678")["name"], v.MSG_NAME_REQUIRED)
        self.assertEqual(v.validate_account_input("0000001", "a" * 30, "12345678"), {})
        self.assertEqual(v.validate_account_input("0000001", "a" * 31, "12345678")["name"], v.MSG_NAME_TOO_LONG)

    def test_password_min_8(self):
        self.assertEqual(v.validate_account_input("0000001", "a", "1234567")["password"], v.MSG_PASSWORD_TOO_SHORT)
        self.assertEqual(v.validate_account_input("0000001", "a", "12345678"), {})


class LendingValidationTest(unittest.TestCase):
    TODAY = date(2026, 11, 5)

    def test_valid_lending_has_no_errors(self):
        self.assertEqual(v.validate_lending_input("0000001", "2026-11-05", self.TODAY), {})
        self.assertEqual(v.validate_lending_input("0000001", "2026-01-01", self.TODAY), {})

    def test_borrower_required(self):
        self.assertEqual(
            v.validate_lending_input("", "2026-11-05", self.TODAY)["borrower"], v.MSG_BORROWER_REQUIRED
        )

    def test_future_date_is_rejected(self):
        self.assertEqual(
            v.validate_lending_input("0000001", "2026-11-06", self.TODAY)["lent_on"], v.MSG_LENT_ON_FUTURE
        )

    def test_bad_date_format_is_rejected(self):
        for bad in ["", "2026/11/05", "20261105", "2026-13-01", "2026-02-30", "abc"]:
            self.assertEqual(
                v.validate_lending_input("0000001", bad, self.TODAY)["lent_on"], v.MSG_LENT_ON_FORMAT, bad
            )


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
