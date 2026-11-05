import unittest

import _paths  # noqa: F401
import seed_data
import validation


class SampleSpeciesTest(unittest.TestCase):
    def test_twelve_species_with_unique_scientific_names(self):
        species = seed_data.sample_species_data()
        self.assertEqual(len(species), 12)
        names = [item["scientific_name"].lower() for item in species]
        self.assertEqual(len(set(names)), 12)

    def test_fixed_list_values_and_required_fields(self):
        for item in seed_data.sample_species_data():
            self.assertIn(item["class_name"], validation.CLASS_VALUES)
            self.assertIn(item["habitat"], validation.HABITAT_VALUES)
            self.assertIn(item["diet"], validation.DIET_VALUES)
            self.assertIn(item["conservation_status"], validation.STATUS_LABELS)
            self.assertTrue(item["common_name"])

    def test_sample_values_pass_the_same_checks_as_the_form(self):
        for item in seed_data.sample_species_data():
            form = {key: "" if value is None else str(value) for key, value in item.items()}
            _, errors = validation.validate_species_fields(form)
            self.assertEqual(errors, {}, item["scientific_name"])

    def test_threatened_and_forest_samples_exist_for_the_screens(self):
        species = seed_data.sample_species_data()
        threatened = [s for s in species if s["conservation_status"] in validation.THREATENED_STATUSES]
        self.assertEqual(len(threatened), 6)
        birds_in_forest = [s for s in species if s["class_name"] == "Aves" and s["habitat"] == "Forest"]
        self.assertEqual(len(birds_in_forest), 1)


if __name__ == "__main__":
    unittest.main()
