"""保存クラス（SpeciesStore）の単体テスト。一時フォルダの SQLite を使う。"""

import os
import shutil
import tempfile
import unittest

from src.core.store import SpeciesStore

ALL = {"q": "", "taxonomic_class": "", "habitat": "", "diet": "", "conservation_status": ""}


def _species(**overrides):
    values = {
        "scientific_name": "Testus example",
        "common_name": "Example animal",
        "taxonomic_class": "Fish",
        "habitat": "Marine",
        "diet": "Carnivore",
        "lifespan_years": None,
        "body_mass_kg": None,
        "conservation_status": "Data Deficient",
        "description": "",
    }
    values.update(overrides)
    return values


class SpeciesStoreTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="species-store-test-")
        self.store = SpeciesStore(os.path.join(self.folder, "data", "species.db"))
        self.store.initialize()

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    def test_initialize_seeds_samples_only_once(self):
        self.assertEqual(len(self.store.list_species(ALL)), 12)
        self.store.initialize()
        self.assertEqual(len(self.store.list_species(ALL)), 12)

    def test_list_is_sorted_by_common_name(self):
        names = [row["common_name"] for row in self.store.list_species(ALL)]
        self.assertEqual(names, sorted(names, key=str.lower))

    def test_filters_combine_with_and(self):
        rows = self.store.list_species(dict(ALL, taxonomic_class="Birds", diet="Carnivore"))
        self.assertEqual(sorted(r["common_name"] for r in rows), ["Bald eagle", "Emperor penguin"])

    def test_keyword_searches_name_and_description_and_escapes_wildcards(self):
        rows = self.store.list_species(dict(ALL, q="SALMON"))
        self.assertEqual([r["common_name"] for r in rows], ["Atlantic salmon"])
        self.assertEqual(self.store.list_species(dict(ALL, q="%")), [])
        self.assertEqual(self.store.list_species(dict(ALL, q="_")), [])

    def test_create_update_delete_round_trip(self):
        new_id = self.store.create_species(_species())
        self.assertEqual(self.store.get_species(new_id)["common_name"], "Example animal")
        self.assertTrue(self.store.update_species(new_id, _species(common_name="Renamed")))
        self.assertEqual(self.store.get_species(new_id)["common_name"], "Renamed")
        self.assertTrue(self.store.delete_species(new_id))
        self.assertIsNone(self.store.get_species(new_id))
        self.assertFalse(self.store.delete_species(new_id))
        self.assertFalse(self.store.update_species(new_id, _species()))

    def test_scientific_name_is_unique_ignoring_case_and_spaces(self):
        self.store.create_species(_species(scientific_name="Testus example"))
        self.assertTrue(self.store.is_scientific_name_taken("  TESTUS EXAMPLE "))
        with self.assertRaises(Exception):
            self.store.create_species(_species(scientific_name="testus EXAMPLE"))

    def test_taken_check_ignores_the_species_itself(self):
        new_id = self.store.create_species(_species(scientific_name="Own name"))
        self.assertFalse(self.store.is_scientific_name_taken("Own name", new_id))
        self.assertTrue(self.store.is_scientific_name_taken("Own name", None))


if __name__ == "__main__":
    unittest.main()
