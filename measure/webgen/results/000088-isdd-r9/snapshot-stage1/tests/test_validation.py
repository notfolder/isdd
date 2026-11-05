import unittest

import _paths  # noqa: F401  (adds src/ to sys.path)
import validation


def valid_form(**overrides):
    form = {
        "scientific_name": "Panthera leo",
        "common_name": "Lion",
        "class_name": "Mammalia",
        "family": "Felidae",
        "habitat": "Grassland",
        "diet": "Carnivore",
        "conservation_status": "VU",
        "average_lifespan_years": "14",
        "average_adult_mass_kg": "190.5",
        "description": "Large social cat.",
    }
    form.update(overrides)
    return form


class ValidateSpeciesFieldsTest(unittest.TestCase):
    def test_valid_form_is_cleaned(self):
        cleaned, errors = validation.validate_species_fields(valid_form(scientific_name="  Panthera leo  "))
        self.assertEqual(errors, {})
        self.assertEqual(cleaned["scientific_name"], "Panthera leo")
        self.assertEqual(cleaned["average_lifespan_years"], 14)
        self.assertEqual(cleaned["average_adult_mass_kg"], 190.5)

    def test_optional_fields_empty_become_none_or_blank(self):
        cleaned, errors = validation.validate_species_fields(
            valid_form(family="", average_lifespan_years="", average_adult_mass_kg="", description=""))
        self.assertEqual(errors, {})
        self.assertIsNone(cleaned["average_lifespan_years"])
        self.assertIsNone(cleaned["average_adult_mass_kg"])
        self.assertEqual(cleaned["family"], "")
        self.assertEqual(cleaned["description"], "")

    def test_required_names_are_checked(self):
        _, errors = validation.validate_species_fields(valid_form(scientific_name="A", common_name=""))
        self.assertIn("scientific_name", errors)
        self.assertIn("common_name", errors)
        _, errors = validation.validate_species_fields(valid_form(scientific_name=""))
        self.assertIn("scientific_name", errors)

    def test_name_length_limits(self):
        _, errors = validation.validate_species_fields(valid_form(scientific_name="x" * 101))
        self.assertIn("scientific_name", errors)
        _, errors = validation.validate_species_fields(valid_form(common_name="x" * 101))
        self.assertIn("common_name", errors)

    def test_choices_must_be_from_fixed_lists(self):
        _, errors = validation.validate_species_fields(valid_form(class_name="Fish", habitat="Mountain",
                                                                  diet="Vegan", conservation_status="XX"))
        self.assertEqual(set(errors), {"class_name", "habitat", "diet", "conservation_status"})

    def test_lifespan_must_be_whole_number_from_1_to_300(self):
        for value in ("0", "301", "1.5", "abc", "-3"):
            _, errors = validation.validate_species_fields(valid_form(average_lifespan_years=value))
            self.assertIn("average_lifespan_years", errors, value)
        _, errors = validation.validate_species_fields(valid_form(average_lifespan_years="300"))
        self.assertNotIn("average_lifespan_years", errors)

    def test_mass_must_be_positive_up_to_200000_with_two_decimals(self):
        for value in ("0", "-1", "200000.01", "1.234", "abc", "NaN", "Infinity"):
            _, errors = validation.validate_species_fields(valid_form(average_adult_mass_kg=value))
            self.assertIn("average_adult_mass_kg", errors, value)
        for value in ("0.01", "200000", "190.50", "190.0"):
            _, errors = validation.validate_species_fields(valid_form(average_adult_mass_kg=value))
            self.assertNotIn("average_adult_mass_kg", errors, value)

    def test_family_and_description_length_limits(self):
        _, errors = validation.validate_species_fields(valid_form(family="f" * 101))
        self.assertIn("family", errors)
        _, errors = validation.validate_species_fields(valid_form(description="d" * 1001))
        self.assertIn("description", errors)
        _, errors = validation.validate_species_fields(valid_form(description="d" * 1000))
        self.assertNotIn("description", errors)

    def test_all_errors_are_reported_together(self):
        _, errors = validation.validate_species_fields({})
        self.assertGreaterEqual(len(errors), 6)


class ParseSearchQueryTest(unittest.TestCase):
    def test_text_is_trimmed_and_lowercased(self):
        result = validation.parse_search_query({"q": "  Lion  "})
        self.assertEqual(result, {"text": "lion", "filters": {}})

    def test_all_and_unknown_values_are_ignored(self):
        result = validation.parse_search_query({"class_name": "", "habitat": "All", "diet": "Vegan",
                                                "conservation_status": "VU"})
        self.assertEqual(result["filters"], {"conservation_status": "VU"})

    def test_valid_filters_are_kept(self):
        result = validation.parse_search_query({"class_name": "Aves", "habitat": "Forest", "diet": "Insectivore"})
        self.assertEqual(result["filters"], {"class_name": "Aves", "habitat": "Forest", "diet": "Insectivore"})


class FixedListTest(unittest.TestCase):
    def test_threatened_statuses_are_in_status_labels(self):
        for code in validation.THREATENED_STATUSES:
            self.assertIn(code, validation.STATUS_LABELS)


if __name__ == "__main__":
    unittest.main()
