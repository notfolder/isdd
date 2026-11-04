"""入力の読み取りと検証の単体テスト。"""

import unittest

from app.validation import SpeciesForm, parse_species_form, validate_species_form


def _valid_data(**overrides: str) -> dict[str, str]:
    data = {
        "scientific_name": "  Vulpes vulpes  ",
        "common_name": "Red fox",
        "kingdom": "Animalia",
        "taxonomic_class": "Mammalia",
        "habitat": "Terrestrial",
        "diet": "Omnivore",
        "conservation_status": "LC",
        "average_length_cm": "70.5",
        "description": "Adaptable fox.",
    }
    data.update(overrides)
    return data


class _FakeRepository:
    """学名の重複判定だけを持つ代わり（テスト用）。"""

    def __init__(self, taken: dict[str, int]) -> None:
        self._taken = {name.lower(): value for name, value in taken.items()}

    def find_id_by_scientific_name(self, scientific_name: str, exclude_id=None):
        found = self._taken.get(scientific_name.lower())
        return None if found == exclude_id else found


class ParseTest(unittest.TestCase):
    def test_values_are_stripped(self) -> None:
        form = parse_species_form(_valid_data())
        self.assertEqual(form.scientific_name, "Vulpes vulpes")

    def test_missing_fields_default_to_empty(self) -> None:
        form = parse_species_form({})
        self.assertEqual(form.common_name, "")


class ValidateTest(unittest.TestCase):
    def _errors(self, repository=None, exclude_id=None, **overrides: str) -> dict[str, str]:
        form = parse_species_form(_valid_data(**overrides))
        validate_species_form(form, repository, exclude_id)
        return form.errors

    def test_valid_form_has_no_errors(self) -> None:
        self.assertEqual(self._errors(), {})

    def test_required_fields(self) -> None:
        errors = self._errors(scientific_name="", common_name="")
        self.assertIn("scientific_name", errors)
        self.assertIn("common_name", errors)

    def test_name_length_limit(self) -> None:
        self.assertIn("scientific_name", self._errors(scientific_name="x" * 101))
        self.assertIn("common_name", self._errors(common_name="x" * 101))

    def test_selection_must_be_in_list(self) -> None:
        errors = self._errors(kingdom="Dragon", habitat="Sky", diet="Rocks", conservation_status="XX")
        for name in ("kingdom", "habitat", "diet", "conservation_status"):
            self.assertEqual(errors[name], "Please select a value from the list.")

    def test_class_and_description_length_limits(self) -> None:
        self.assertIn("taxonomic_class", self._errors(taxonomic_class="c" * 61))
        self.assertIn("description", self._errors(description="d" * 2001))

    def test_average_length_rules(self) -> None:
        for bad in ("0", "0.0", "-1", "100001", "1.25", "abc", ".5"):
            self.assertIn("average_length_cm", self._errors(average_length_cm=bad), bad)
        for good in ("0.1", "1", "100000"):
            self.assertNotIn("average_length_cm", self._errors(average_length_cm=good), good)
        self.assertNotIn("average_length_cm", self._errors(average_length_cm=""))

    def test_duplicate_scientific_name_is_rejected(self) -> None:
        repo = _FakeRepository({"Vulpes vulpes": 5})
        self.assertEqual(self._errors(repo)["scientific_name"], "This scientific name is already registered.")

    def test_own_scientific_name_is_not_a_duplicate_when_editing(self) -> None:
        repo = _FakeRepository({"Vulpes vulpes": 5})
        self.assertEqual(self._errors(repo, exclude_id=5), {})

    def test_field_values_excludes_errors(self) -> None:
        form = SpeciesForm(scientific_name="A")
        self.assertNotIn("errors", form.field_values())


if __name__ == "__main__":
    unittest.main()
