"""結合テスト: WheelService と一時 DB を組み合わせ、抽選と当選記録が一致することを確かめる。"""

import os
import random
import tempfile
import unittest
from datetime import datetime

import _path  # noqa: F401
from service.validation import PlayerNameError
from service.wheel import WheelService
from store.database import Database
from store.repositories import RecordRepository
from store.seed import SAMPLE_PLAYER_NAME, SAMPLE_PRIZES, seed_sample_data


class WheelServiceIntegrationTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.database = Database(os.path.join(self._tmp.name, "wheel.db"))
        self.database.init_schema()
        seed_sample_data(self.database)
        self.clock_time = datetime(2026, 11, 5, 12, 0, 0)
        self.records = RecordRepository(self.database)

    def tearDown(self):
        self._tmp.cleanup()

    def service(self, seed):
        return WheelService(self.database, rng=random.Random(seed), clock=lambda: self.clock_time)

    def test_probabilities_sum_to_one_hundred(self):
        prizes = self.service(1).list_prizes()
        self.assertEqual(len(prizes), len(SAMPLE_PRIZES))
        self.assertAlmostEqual(sum(p["probability_percent"] for p in prizes), 100.0, places=6)

    def test_records_grow_exactly_by_winning_spins(self):
        service = self.service(7)
        before = len(self.records.find_by_player("Integration"))
        wins = 0
        misses = 0
        for _ in range(200):
            outcome = service.spin("Integration")
            if outcome["is_miss"]:
                self.assertIsNone(outcome["record_id"])
                misses += 1
            else:
                self.assertIsNotNone(outcome["record_id"])
                wins += 1
        self.assertGreater(wins, 0)
        self.assertGreater(misses, 0)
        self.assertEqual(len(self.records.find_by_player("Integration")) - before, wins)

    def test_winning_record_has_time_and_prize_name(self):
        outcome = None
        service = self.service(3)
        for _ in range(50):
            outcome = service.spin("Integration")
            if not outcome["is_miss"]:
                break
        self.assertFalse(outcome["is_miss"])
        record = self.records.find_by_player("Integration")[0]
        self.assertEqual(record["prize_name"], outcome["prize_name"])
        self.assertEqual(record["won_at"], "2026-11-05 12:00:00")

    def test_invalid_name_records_nothing(self):
        service = self.service(2)
        before = self.records.count()
        for raw in ["", "   ", "x" * 21]:
            with self.assertRaises(PlayerNameError):
                service.spin(raw)
        self.assertEqual(self.records.count(), before)

    def test_list_records_returns_seeded_history_for_sample_player(self):
        records = self.service(4).list_records(SAMPLE_PLAYER_NAME)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["won_at"], "2026-11-05 09:15:00")

    def test_list_records_adds_the_player_name_to_each_record(self):
        service = self.service(4)
        name = "  Name Check  "
        for _ in range(30):
            service.spin(name)
        records = service.list_records(name)
        self.assertTrue(records)
        for record in records:
            self.assertEqual(record["player_name"], "Name Check")
            self.assertIn("prize_name", record)
            self.assertIn("won_at", record)


if __name__ == "__main__":
    unittest.main()
