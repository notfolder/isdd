"""一覧の並べ替え（純粋な関数 sort_species_rows と並べ替えの値）の単体テスト。"""

import unittest

from app.sorting import DEFAULT_SORT_ORDER, SORT_ORDERS, sort_species_rows


def _row(row_id: int, common: str, scientific=None) -> dict:
    return {"id": row_id, "common_name": common, "scientific_name": scientific}


class SortSpeciesRowsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = [
            _row(1, "wolf", "Canis lupus"),
            _row(2, "Antelope", None),
            _row(3, "bear", "Ursus arctos"),
            _row(4, "Zebra", "Equus quagga"),
        ]

    def names(self, rows) -> list[str]:
        return [row["common_name"] for row in rows]

    def test_ascending_ignores_case(self) -> None:
        self.assertEqual(self.names(sort_species_rows(self.rows, "name_asc")), ["Antelope", "bear", "wolf", "Zebra"])

    def test_descending_is_reverse_of_ascending(self) -> None:
        self.assertEqual(self.names(sort_species_rows(self.rows, "name_desc")), ["Zebra", "wolf", "bear", "Antelope"])

    def test_same_name_is_ordered_by_scientific_name_then_empty_last(self) -> None:
        rows = [_row(1, "Lion", None), _row(2, "Lion", "Panthera leo"), _row(3, "Lion", "Panthera atrox")]
        asc = sort_species_rows(rows, "name_asc")
        self.assertEqual([row["id"] for row in asc], [3, 2, 1])

    def test_returns_new_list_and_keeps_input(self) -> None:
        before = list(self.rows)
        result = sort_species_rows(self.rows, "name_asc")
        self.assertIsNot(result, self.rows)
        self.assertEqual(self.rows, before)

    def test_empty_input(self) -> None:
        self.assertEqual(sort_species_rows([], "name_desc"), [])

    def test_options_and_default(self) -> None:
        self.assertEqual(DEFAULT_SORT_ORDER, "name_asc")
        self.assertEqual(set(SORT_ORDERS), {"name_asc", "name_desc"})


if __name__ == "__main__":
    unittest.main()
