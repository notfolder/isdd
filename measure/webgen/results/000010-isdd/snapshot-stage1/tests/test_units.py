"""単体・結合テスト。一時ディレクトリの DB を使う。"""

import os
import sqlite3
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.db import SAMPLE_PRIZES, open_database  # noqa: E402
from app.draw import draw_prize  # noqa: E402
from app.repository import find_records_by_name, insert_spin_record, list_prizes  # noqa: E402
from app.server import handle_prizes, handle_records, handle_spin, serve_static  # noqa: E402
from app.validation import validate_player_name  # noqa: E402


class ValidatePlayerNameTest(unittest.TestCase):
    def test_strips_and_accepts_1_to_30(self):
        self.assertEqual(validate_player_name("  Alice  "), "Alice")
        self.assertEqual(validate_player_name("a" * 30), "a" * 30)

    def test_rejects_empty_blank_long_and_non_string(self):
        for value in ["", "   ", "a" * 31, None, 12]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_player_name(value)


class DrawPrizeTest(unittest.TestCase):
    def test_returns_index_within_range(self):
        for _ in range(50):
            self.assertIn(draw_prize(["a", "b", "c"]), [0, 1, 2])

    def test_empty_list_raises(self):
        with self.assertRaises(ValueError):
            draw_prize([])


class DatabaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data_dir = os.path.join(self.tmp.name, "data")

    def tearDown(self):
        self.tmp.cleanup()

    def test_new_database_gets_sample_prizes(self):
        path = open_database(self.data_dir)
        prizes = list_prizes(path)
        self.assertEqual([p["name"] for p in prizes], [name for name, _ in SAMPLE_PRIZES])
        self.assertEqual(len(prizes), 6)

    def test_second_open_keeps_existing_prizes(self):
        path = open_database(self.data_dir)
        connection = sqlite3.connect(path)
        with connection:
            connection.execute("DELETE FROM prize")
        connection.close()
        open_database(self.data_dir)
        self.assertEqual(list_prizes(path), [])


class RepositoryAndHandlersTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = open_database(os.path.join(self.tmp.name, "data"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_insert_and_find_newest_first_with_exact_name(self):
        insert_spin_record(self.path, "Alice", 1, "Coffee Voucher", "2026-01-01T00:00:00Z")
        insert_spin_record(self.path, "Alice", 2, "Gift Card 500", "2026-01-02T00:00:00Z")
        insert_spin_record(self.path, "Bob", 3, "Tote Bag", "2026-01-03T00:00:00Z")
        records = find_records_by_name(self.path, "Alice")
        self.assertEqual([r["prize_name"] for r in records], ["Gift Card 500", "Coffee Voucher"])
        self.assertEqual(find_records_by_name(self.path, "alice"), [])

    def test_spin_success_records_one_entry(self):
        status, body = handle_spin(self.path, b'{"player_name": "Alice"}')
        self.assertEqual(status, 200)
        self.assertIn(body["prize"]["name"], [name for name, _ in SAMPLE_PRIZES])
        self.assertEqual(body["record"]["player_name"], "Alice")
        self.assertEqual(len(find_records_by_name(self.path, "Alice")), 1)

    def test_spin_invalid_name_is_400_and_records_nothing(self):
        status, body = handle_spin(self.path, b'{"player_name": "   "}')
        self.assertEqual(status, 400)
        self.assertIn("1–30 characters", body["error"])
        self.assertEqual(find_records_by_name(self.path, ""), [])

    def test_spin_with_no_prizes_is_409(self):
        connection = sqlite3.connect(self.path)
        with connection:
            connection.execute("DELETE FROM prize")
        connection.close()
        status, body = handle_spin(self.path, b'{"player_name": "Alice"}')
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "No prizes are available")

    def test_spin_bad_json_is_400(self):
        status, body = handle_spin(self.path, b"not json")
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "Invalid request")

    def test_records_requires_name(self):
        status, body = handle_records(self.path, "player_name=")
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "Please enter your name")

    def test_prizes_handler_returns_list(self):
        status, body = handle_prizes(self.path)
        self.assertEqual(status, 200)
        self.assertEqual(len(body["prizes"]), 6)

    def test_static_known_and_unknown(self):
        status, content_type, body = serve_static("/")
        self.assertEqual(status, 200)
        self.assertIn(b"Wheel of Fortune", body)
        self.assertTrue(content_type.startswith("text/html"))
        self.assertEqual(serve_static("/nope.txt")[0], 404)


if __name__ == "__main__":
    unittest.main()
