"""Unit tests for input validation (rules D7 to D9)."""

import unittest

from core.validation import (
    ValidationError,
    normalize_phone,
    validate_barber_form,
    validate_notify_form,
    validate_service_form,
)


class BarberFormTests(unittest.TestCase):
    def test_valid_barber(self):
        data = validate_barber_form({"name": " Ana ", "specialty": "Fades", "phone": "+1 555 0100"})
        self.assertEqual(data, {"name": "Ana", "specialty": "Fades", "phone": "+1 555 0100"})

    def test_phone_is_optional(self):
        data = validate_barber_form({"name": "Ana"})
        self.assertEqual(data["phone"], "")

    def test_empty_name_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_barber_form({"name": "   "})
        self.assertIn("Name is required.", ctx.exception.errors)

    def test_long_name_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_barber_form({"name": "x" * 61})

    def test_invalid_phone_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_barber_form({"name": "Ana", "phone": "abc"})
        self.assertTrue(any("not valid" in e for e in ctx.exception.errors))

    def test_all_errors_are_reported_together(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_barber_form({"name": "", "specialty": "x" * 101, "phone": "1"})
        self.assertEqual(len(ctx.exception.errors), 3)


class ServiceFormTests(unittest.TestCase):
    def test_valid_service_converts_price_to_cents(self):
        data = validate_service_form({"name": "Cut", "price": "12.50", "duration_min": "20"})
        self.assertEqual(data["price_cents"], 1250)
        self.assertEqual(data["duration_min"], 20)
        self.assertEqual(data["description"], "")

    def test_price_zero_is_allowed(self):
        self.assertEqual(validate_service_form({"name": "Free", "price": "0", "duration_min": "5"})["price_cents"], 0)

    def test_negative_price_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_service_form({"name": "Cut", "price": "-1", "duration_min": "20"})
        self.assertIn("Price must be between 0 and 10000.", ctx.exception.errors)

    def test_price_with_three_decimals_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_service_form({"name": "Cut", "price": "1.234", "duration_min": "20"})

    def test_price_not_a_number_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_service_form({"name": "Cut", "price": "abc", "duration_min": "20"})

    def test_price_above_limit_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_service_form({"name": "Cut", "price": "10000.01", "duration_min": "20"})

    def test_duration_bounds(self):
        for bad in ("4", "481", "2.5", "abc", ""):
            with self.assertRaises(ValidationError, msg=bad):
                validate_service_form({"name": "Cut", "price": "1", "duration_min": bad})
        self.assertEqual(validate_service_form({"name": "Cut", "price": "1", "duration_min": "480"})["duration_min"], 480)

    def test_missing_name_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_service_form({"name": "", "price": "1", "duration_min": "5"})


class NotifyFormTests(unittest.TestCase):
    def test_numbers_split_by_lines_and_commas(self):
        data = validate_notify_form({"phones": "+1 555 0101\n+81-90-5555-0103, +1 (555) 0199", "message": "Hi"})
        self.assertEqual(data["numbers"], ["15550101", "819055550103", "15550199"])
        self.assertEqual(data["message"], "Hi")

    def test_one_bad_number_rejects_the_whole_list(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_notify_form({"phones": "+15550101\nabc", "message": "Hi"})
        self.assertEqual(len(ctx.exception.errors), 1)

    def test_empty_numbers_rejected(self):
        with self.assertRaises(ValidationError):
            validate_notify_form({"phones": " \n ", "message": "Hi"})

    def test_more_than_twenty_numbers_rejected(self):
        phones = "\n".join("+1555010%02d" % i for i in range(21))
        with self.assertRaises(ValidationError):
            validate_notify_form({"phones": phones, "message": "Hi"})

    def test_empty_message_rejected(self):
        with self.assertRaises(ValidationError):
            validate_notify_form({"phones": "+15550101", "message": ""})

    def test_long_message_rejected(self):
        with self.assertRaises(ValidationError):
            validate_notify_form({"phones": "+15550101", "message": "x" * 501})


class PhoneTests(unittest.TestCase):
    def test_normalize_phone(self):
        self.assertEqual(normalize_phone("+1 (555) 010-0101"), "15550100101")
        self.assertIsNone(normalize_phone("12345"))  # too short
        self.assertIsNone(normalize_phone("+1555010010199999"))  # too long
        self.assertIsNone(normalize_phone("1555 abc 0101"))


if __name__ == "__main__":
    unittest.main()
