import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from store import SAMPLE_PRIZES, Store  # noqa: E402


class StoreTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.store = Store(os.path.join(self._tmp.name, "data", "wheel.sqlite3"))

    def tearDown(self):
        self._tmp.cleanup()

    def test_seeds_sample_prizes_once(self):
        self.assertTrue(self.store.seed_sample_prizes())
        self.assertFalse(self.store.seed_sample_prizes())
        prizes = self.store.list_prizes()
        self.assertEqual(len(prizes), len(SAMPLE_PRIZES))
        self.assertEqual(sum(p["weight"] for p in prizes), 100)

    def test_winnings_are_per_player_newest_first(self):
        self.store.add_winning("a" * 32, "Ann", "Free Coffee", "2026-11-05T01:00:00Z")
        self.store.add_winning("a" * 32, "Ann", "Tote Bag", "2026-11-05T02:00:00Z")
        self.store.add_winning("b" * 32, "Ben", "Sticker Pack", "2026-11-05T03:00:00Z")
        mine = self.store.list_winnings("a" * 32)
        self.assertEqual([r["prize_name"] for r in mine], ["Tote Bag", "Free Coffee"])
        self.assertEqual(self.store.list_winnings("c" * 32), [])


if __name__ == "__main__":
    unittest.main()
