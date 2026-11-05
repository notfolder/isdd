"""データ層の単体テスト: 初期化、景品の一覧、当選記録の追加と絞り込み。"""

import os
import sqlite3
import tempfile
import unittest

from app.database import SAMPLE_PRIZES, Database


class DatabaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self._tmp.name, "wheel.sqlite3")
        self.db = Database(self.path)
        self.db.initialize()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_initialize_inserts_sample_prizes_once(self) -> None:
        self.assertEqual(len(self.db.list_prizes()), len(SAMPLE_PRIZES))
        self.db.initialize()
        self.assertEqual(len(self.db.list_prizes()), len(SAMPLE_PRIZES))

    def test_initialize_inserts_sample_records_once(self) -> None:
        self.assertEqual(len(self.db.list_winnings_by_name("Sample Player")), 3)
        self.db.initialize()
        self.assertEqual(len(self.db.list_winnings_by_name("Sample Player")), 3)

    def test_list_prizes_is_in_display_order(self) -> None:
        names = [prize["name"] for prize in self.db.list_prizes()]
        self.assertEqual(names, [name for name, _ in SAMPLE_PRIZES])

    def test_add_winning_record_then_find_by_name_ignoring_case(self) -> None:
        prize = self.db.list_prizes()[0]
        record = self.db.add_winning_record("Alice", prize)
        self.assertEqual(record["player_name"], "Alice")
        self.assertEqual(record["prize_name"], prize["name"])
        self.assertTrue(record["won_at"].endswith("Z"))

        found = self.db.list_winnings_by_name("aLICE")
        self.assertEqual([row["id"] for row in found], [record["id"]])

    def test_winnings_do_not_include_other_names(self) -> None:
        prize = self.db.list_prizes()[0]
        self.db.add_winning_record("Alice", prize)
        self.assertEqual(self.db.list_winnings_by_name("Bob"), [])

    def test_winnings_are_newest_first(self) -> None:
        prize = self.db.list_prizes()[0]
        first = self.db.add_winning_record("Carol", prize)
        second = self.db.add_winning_record("Carol", prize)
        ids = [row["id"] for row in self.db.list_winnings_by_name("Carol")]
        self.assertEqual(ids, [second["id"], first["id"]])

    def test_user_name_is_bound_as_parameter(self) -> None:
        prize = self.db.list_prizes()[0]
        hostile = "x'); DROP TABLE prizes; --"
        self.db.add_winning_record(hostile, prize)
        conn = sqlite3.connect(self.path)
        try:
            count = conn.execute("SELECT COUNT(*) FROM prizes").fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(count, len(SAMPLE_PRIZES))
        self.assertEqual(len(self.db.list_winnings_by_name(hostile)), 1)


if __name__ == "__main__":
    unittest.main()
