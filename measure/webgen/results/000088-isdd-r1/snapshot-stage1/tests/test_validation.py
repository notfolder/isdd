"""入力チェックと検索条件の読み取りの単体テスト。"""

import unittest

from src.core.validation import read_filter_conditions, validate_species_input


def _valid_values(**overrides):
    values = {
        "scientific_name": "  Panthera leo  ",
        "common_name": " Lion ",
        "taxonomic_class": "Mammals",
        "habitat": "Grassland",
        "diet": "Carnivore",
        "lifespan_years": "14",
        "body_mass_kg": "190.5",
        "conservation_status": "Vulnerable",
        "description": "  Large cat of Africa and India.  ",
    }
    values.update(overrides)
    return values


def _never_taken(_name):
    return False


class ValidateSpeciesInputTest(unittest.TestCase):
    def test_valid_input_is_cleaned(self):
        cleaned, errors = validate_species_input(_valid_values(), _never_taken)
        self.assertEqual(errors, [])
        self.assertEqual(cleaned["scientific_name"], "Panthera leo")
        self.assertEqual(cleaned["common_name"], "Lion")
        self.assertEqual(cleaned["lifespan_years"], 14)
        self.assertEqual(cleaned["body_mass_kg"], 190.5)
        self.assertEqual(cleaned["description"], "Large cat of Africa and India.")

    def test_optional_fields_become_none_when_blank(self):
        cleaned, errors = validate_species_input(
            _valid_values(lifespan_years="", body_mass_kg="  ", description=""), _never_taken
        )
        self.assertEqual(errors, [])
        self.assertIsNone(cleaned["lifespan_years"])
        self.assertIsNone(cleaned["body_mass_kg"])

    def test_required_fields_are_reported(self):
        values = _valid_values(scientific_name="", common_name="", habitat="", conservation_status="")
        _cleaned, errors = validate_species_input(values, _never_taken)
        self.assertIn("Scientific name is required.", errors)
        self.assertIn("Common name is required.", errors)
        self.assertIn("Habitat is required.", errors)
        self.assertIn("Conservation status is required.", errors)

    def test_choice_outside_list_is_rejected(self):
        _cleaned, errors = validate_species_input(_valid_values(diet="Plants"), _never_taken)
        self.assertEqual(errors, ["Diet must be one of the listed values."])

    def test_duplicate_scientific_name_uses_the_check_function(self):
        seen = []

        def taken(name):
            seen.append(name)
            return True

        _cleaned, errors = validate_species_input(_valid_values(), taken)
        self.assertEqual(errors, ["Scientific name already exists."])
        self.assertEqual(seen, ["Panthera leo"])

    def test_name_and_description_lengths(self):
        _cleaned, errors = validate_species_input(
            _valid_values(scientific_name="A" * 101, common_name="B" * 101, description="C" * 1001),
            _never_taken,
        )
        self.assertIn("Scientific name must be 100 characters or fewer.", errors)
        self.assertIn("Common name must be 100 characters or fewer.", errors)
        self.assertIn("Description must be 1000 characters or fewer.", errors)

    def test_lifespan_range(self):
        message = "Lifespan must be a whole number from 1 to 500."
        for raw in ["0", "501", "abc", "12.5", "-3"]:
            _cleaned, errors = validate_species_input(_valid_values(lifespan_years=raw), _never_taken)
            self.assertIn(message, errors, raw)
        for raw in ["1", "500"]:
            _cleaned, errors = validate_species_input(_valid_values(lifespan_years=raw), _never_taken)
            self.assertEqual(errors, [], raw)

    def test_body_mass_range(self):
        message = "Body mass must be a number greater than 0 and at most 200000."
        for raw in ["0", "-1", "200001", "nan", "inf", "heavy"]:
            _cleaned, errors = validate_species_input(_valid_values(body_mass_kg=raw), _never_taken)
            self.assertIn(message, errors, raw)
        for raw in ["0.05", "200000"]:
            _cleaned, errors = validate_species_input(_valid_values(body_mass_kg=raw), _never_taken)
            self.assertEqual(errors, [], raw)


class ReadFilterConditionsTest(unittest.TestCase):
    def test_known_values_are_kept(self):
        conditions = read_filter_conditions(
            {"q": "  wolf ", "taxonomic_class": "Birds", "habitat": "Marine", "diet": "Omnivore",
             "conservation_status": "Endangered"}
        )
        self.assertEqual(
            conditions,
            {"q": "wolf", "taxonomic_class": "Birds", "habitat": "Marine", "diet": "Omnivore",
             "conservation_status": "Endangered"},
        )

    def test_unknown_choice_is_treated_as_all(self):
        conditions = read_filter_conditions({"taxonomic_class": "Plants"})
        self.assertEqual(conditions["taxonomic_class"], "")
        self.assertEqual(conditions["q"], "")


if __name__ == "__main__":
    unittest.main()
