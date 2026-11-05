"""重みによる区分の選択の単体テスト（乱数を固定して境界を確かめる）。"""

import unittest

import _path  # noqa: F401
from service.wheel import choose_segment_by_weight


class FixedRandom:
    """randrange の結果を固定する。"""

    def __init__(self, value):
        self.value = value
        self.bound_seen = None

    def randrange(self, bound):
        self.bound_seen = bound
        return self.value


class ChooseSegmentByWeightTest(unittest.TestCase):
    def test_boundaries_follow_cumulative_weights(self):
        weights = [2, 3, 5]  # 合計 10: [0,1] -> 0, [2,4] -> 1, [5,9] -> 2
        expected = {0: 0, 1: 0, 2: 1, 4: 1, 5: 2, 9: 2}
        for pick, index in expected.items():
            with self.subTest(pick=pick):
                rng = FixedRandom(pick)
                self.assertEqual(choose_segment_by_weight(weights, rng), index)
                self.assertEqual(rng.bound_seen, 10)

    def test_zero_weight_segment_is_never_chosen(self):
        weights = [0, 4]
        for pick in range(4):
            self.assertEqual(choose_segment_by_weight(weights, FixedRandom(pick)), 1)

    def test_rejects_non_positive_total(self):
        with self.assertRaises(ValueError):
            choose_segment_by_weight([0, 0], FixedRandom(0))


if __name__ == "__main__":
    unittest.main()
