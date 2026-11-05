import sqlite3
import tempfile
import unittest

import _paths  # noqa: F401
import validation
from repository import SpeciesRepository


def new_values(**overrides):
    values = {
        "scientific_name": "Vulpes vulpes",
        "common_name": "Red fox",
        "class_name": "Mammalia",
        "family": "Canidae",
        "habitat": "Forest",
        "diet": "Omnivore",
        "conservation_status": "LC",
        "average_lifespan_years": 5,
        "average_adult_mass_kg": 6.5,
        "description": "Adaptable canid.",
    }
    values.update(overrides)
    return values


class SpeciesRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = SpeciesRepository(self.tmp.name)
        self.repo.initialize()

    def tearDown(self):
        self.tmp.cleanup()

    def test_first_initialize_loads_twelve_samples(self):
        self.assertEqual(self.repo.count_species(), 12)

    def test_samples_are_not_loaded_again_on_restart(self):
        self.repo.delete(self.repo.search("", {})[0]["id"])
        self.assertEqual(self.repo.count_species(), 11)
        SpeciesRepository(self.tmp.name).initialize()
        self.assertEqual(self.repo.count_species(), 11)

    def test_count_threatened_species(self):
        self.assertEqual(self.repo.count_threatened_species(), 6)

    def test_create_get_update_delete(self):
        new_id = self.repo.create(new_values())
        stored = self.repo.get(new_id)
        self.assertEqual(stored["common_name"], "Red fox")
        self.assertEqual(stored["average_adult_mass_kg"], 6.5)

        self.assertTrue(self.repo.update(new_id, new_values(common_name="Fox")))
        self.assertEqual(self.repo.get(new_id)["common_name"], "Fox")

        self.assertTrue(self.repo.delete(new_id))
        self.assertIsNone(self.repo.get(new_id))
        self.assertFalse(self.repo.delete(new_id))
        self.assertFalse(self.repo.update(new_id, new_values()))

    def test_scientific_name_is_unique_ignoring_case(self):
        self.assertTrue(self.repo.is_scientific_name_taken("panthera LEO"))
        self.assertFalse(self.repo.is_scientific_name_taken("Panthera tigris"))
        lion_id = [s for s in self.repo.search("", {}) if s["scientific_name"] == "Panthera leo"][0]["id"]
        self.assertFalse(self.repo.is_scientific_name_taken("Panthera leo", exclude_id=lion_id))
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.create(new_values(scientific_name="PANTHERA LEO"))

    def test_search_matches_scientific_or_common_name(self):
        self.assertEqual([s["common_name"] for s in self.repo.search("lion", {})], ["Lion"])
        self.assertEqual([s["scientific_name"] for s in self.repo.search("panthera", {})], ["Panthera leo"])
        self.assertEqual(self.repo.search("zzzz", {}), [])

    def test_search_treats_percent_and_underscore_as_plain_text(self):
        self.assertEqual(self.repo.search("%", {}), [])
        self.assertEqual(self.repo.search("_", {}), [])

    def test_filters_combine_with_and(self):
        birds = self.repo.search("", {"class_name": "Aves"})
        self.assertEqual(len(birds), 3)
        bird_forest = self.repo.search("", {"class_name": "Aves", "habitat": "Forest"})
        self.assertEqual([s["common_name"] for s in bird_forest], ["Japanese bush warbler"])

    def test_results_are_sorted_by_common_name(self):
        names = [s["common_name"] for s in self.repo.search("", {})]
        self.assertEqual(names, sorted(names, key=str.lower))

    def test_unknown_filter_column_is_rejected(self):
        with self.assertRaises(ValueError):
            self.repo.search("", {"name; DROP TABLE species": "x"})

    def test_filter_values_are_from_fixed_lists(self):
        self.assertEqual(set(validation.FILTER_VALUES), {"class_name", "habitat", "diet", "conservation_status"})


if __name__ == "__main__":
    unittest.main()
