"""利用者名の規則の単体テスト。"""

import unittest

import _path  # noqa: F401  (src を import パスに足す)
from service.validation import NAME_ERROR_MESSAGE, PlayerNameError, validate_player_name


class ValidatePlayerNameTest(unittest.TestCase):
    def test_trims_surrounding_spaces(self):
        self.assertEqual(validate_player_name("  Tester A  "), "Tester A")

    def test_accepts_one_and_twenty_characters(self):
        self.assertEqual(validate_player_name("a"), "a")
        self.assertEqual(validate_player_name("x" * 20), "x" * 20)

    def test_rejects_empty_and_blank(self):
        for raw in ["", "   ", "\t"]:
            with self.subTest(raw=raw):
                with self.assertRaises(PlayerNameError) as context:
                    validate_player_name(raw)
                self.assertEqual(str(context.exception), NAME_ERROR_MESSAGE)

    def test_rejects_twenty_one_characters(self):
        with self.assertRaises(PlayerNameError):
            validate_player_name("x" * 21)

    def test_rejects_non_string(self):
        for raw in [None, 5, ["a"]]:
            with self.subTest(raw=raw):
                with self.assertRaises(PlayerNameError):
                    validate_player_name(raw)


if __name__ == "__main__":
    unittest.main()
