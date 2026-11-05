"""データ層（DB の用意、景品と当選記録の読み書き、初期データ）の単体テスト。一時ファイルの SQLite を使う。"""

import os
import tempfile
import unittest

import _path  # noqa: F401
from store.database import Database
from store.repositories import PrizeRepository, RecordRepository
from store.seed import SAMPLE_PLAYER_NAME, SAMPLE_PRIZES, seed_sample_data


class StoreTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.database = Database(os.path.join(self._tmp.name, "wheel.db"))
        self.database.init_schema()
        self.prizes = PrizeRepository(self.database)
        self.records = RecordRepository(self.database)

    def tearDown(self):
        self._tmp.cleanup()

    def test_seed_fills_empty_database_once(self):
        self.assertTrue(seed_sample_data(self.database))
        self.assertEqual(self.prizes.count(), len(SAMPLE_PRIZES))
        self.assertEqual(len(self.records.find_by_player(SAMPLE_PLAYER_NAME)), 2)
        self.assertFalse(seed_sample_data(self.database))
        self.assertEqual(self.prizes.count(), len(SAMPLE_PRIZES))
        self.assertEqual(len(self.records.find_by_player(SAMPLE_PLAYER_NAME)), 2)

    def test_seeded_prizes_are_in_position_order_with_one_miss(self):
        seed_sample_data(self.database)
        prizes = self.prizes.list_all()
        self.assertEqual([p["position"] for p in prizes], list(range(1, len(SAMPLE_PRIZES) + 1)))
        self.assertEqual(sum(p["is_miss"] for p in prizes), 1)

    def test_find_by_player_returns_newest_first_and_matches_exactly(self):
        seed_sample_data(self.database)
        self.records.insert("Other", 1, "10% Off Coupon", "2026-12-01 00:00:00")
        found = self.records.find_by_player(SAMPLE_PLAYER_NAME)
        self.assertEqual([r["won_at"] for r in found], ["2026-11-05 09:15:00", "2026-11-04 18:30:00"])
        self.assertEqual(self.records.find_by_player("sample player"), [])


if __name__ == "__main__":
    unittest.main()
