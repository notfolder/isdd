import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from draw import pick_prize  # noqa: E402

PRIZES = [
    {"id": 1, "name": "A", "weight": 1},
    {"id": 2, "name": "B", "weight": 3},
]


class PickPrizeTest(unittest.TestCase):
    def test_roll_maps_to_weight_ranges(self):
        # Total weight 4: A covers [0, 1), B covers [1, 4) of the scaled roll.
        self.assertEqual(pick_prize(PRIZES, 0.0)["name"], "A")
        self.assertEqual(pick_prize(PRIZES, 0.2)["name"], "A")
        self.assertEqual(pick_prize(PRIZES, 0.26)["name"], "B")
        self.assertEqual(pick_prize(PRIZES, 0.99)["name"], "B")

    def test_empty_list_raises(self):
        with self.assertRaises(ValueError):
            pick_prize([], 0.5)


if __name__ == "__main__":
    unittest.main()
