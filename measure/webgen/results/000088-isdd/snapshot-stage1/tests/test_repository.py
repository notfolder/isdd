"""リポジトリと表の作成の単体テスト。"""

import sqlite3
import tempfile
import unittest

from app.db import connect_database, ensure_database_schema
from app.repository import SpeciesRepository


def _values(**overrides: str) -> dict[str, str]:
    values = {
        "scientific_name": "Vulpes vulpes",
        "common_name": "Red fox",
        "kingdom": "Animalia",
        "taxonomic_class": "Mammalia",
        "habitat": "Terrestrial",
        "diet": "Omnivore",
        "conservation_status": "LC",
        "average_length_cm": "70.5",
        "description": "Adaptable fox.",
    }
    values.update(overrides)
    return values


class RepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.connection = connect_database(self._dir.name)
        ensure_database_schema(self.connection)
        self.repo = SpeciesRepository(self.connection)

    def tearDown(self) -> None:
        self.connection.close()
        self._dir.cleanup()

    def test_schema_creates_species_table_and_is_idempotent(self) -> None:
        ensure_database_schema(self.connection)
        names = [row[0] for row in self.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        self.assertIn("species", names)

    def test_insert_returns_id_and_get_returns_row(self) -> None:
        new_id = self.repo.insert(_values())
        row = self.repo.get(new_id)
        self.assertIsNotNone(row)
        self.assertEqual(row["common_name"], "Red fox")
        self.assertEqual(row["average_length_cm"], 70.5)

    def test_empty_optional_fields_are_stored_as_null(self) -> None:
        new_id = self.repo.insert(_values(taxonomic_class="", average_length_cm="", description=""))
        row = self.repo.get(new_id)
        self.assertIsNone(row["taxonomic_class"])
        self.assertIsNone(row["average_length_cm"])
        self.assertIsNone(row["description"])

    def test_duplicate_scientific_name_is_rejected_case_insensitively(self) -> None:
        self.repo.insert(_values())
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.insert(_values(scientific_name="vulpes VULPES"))

    def test_find_id_by_scientific_name_respects_exclude_id(self) -> None:
        new_id = self.repo.insert(_values())
        self.assertEqual(self.repo.find_id_by_scientific_name("VULPES vulpes"), new_id)
        self.assertIsNone(self.repo.find_id_by_scientific_name("VULPES vulpes", exclude_id=new_id))
        self.assertIsNone(self.repo.find_id_by_scientific_name("Canis lupus"))

    def test_search_keyword_is_case_insensitive_partial_match(self) -> None:
        self.repo.insert(_values())
        self.repo.insert(_values(scientific_name="Canis lupus", common_name="Grey wolf", description="Pack hunter."))
        self.assertEqual([r["common_name"] for r in self.repo.search("RED")], ["Red fox"])
        self.assertEqual([r["common_name"] for r in self.repo.search("pack")], ["Grey wolf"])
        self.assertEqual(self.repo.search("zzzz"), [])

    def test_search_combines_keyword_and_criteria_with_and(self) -> None:
        self.repo.insert(_values())
        self.repo.insert(_values(scientific_name="Canis lupus", common_name="Grey wolf", diet="Carnivore", description="Pack hunter."))
        self.assertEqual(len(self.repo.search("", {"diet": "Carnivore"})), 1)
        self.assertEqual(len(self.repo.search("fox", {"diet": "Carnivore"})), 0)
        self.assertEqual(len(self.repo.search("", {"kingdom": "Plantae"})), 0)

    def test_update_changes_row(self) -> None:
        new_id = self.repo.insert(_values())
        self.repo.update(new_id, _values(common_name="Arctic fox"))
        self.assertEqual(self.repo.get(new_id)["common_name"], "Arctic fox")

    def test_delete_returns_true_only_when_row_existed(self) -> None:
        new_id = self.repo.insert(_values())
        self.assertTrue(self.repo.delete(new_id))
        self.assertFalse(self.repo.delete(new_id))
        self.assertIsNone(self.repo.get(new_id))

    def test_get_missing_returns_none(self) -> None:
        self.assertIsNone(self.repo.get(999))


if __name__ == "__main__":
    unittest.main()
