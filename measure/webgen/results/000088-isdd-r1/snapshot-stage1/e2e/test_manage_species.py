"""登録・修正・削除と入力エラーの E2E テスト。"""

import unittest

from e2e.harness import SiteServer, result_count

VALID_FORM = {
    "scientific_name": "Testus examplea",
    "common_name": "Example animal",
    "taxonomic_class": "Birds",
    "habitat": "Forest",
    "diet": "Omnivore",
    "lifespan_years": "9",
    "body_mass_kg": "2.5",
    "conservation_status": "Near Threatened",
    "description": "Added during the end-to-end test.",
}


class ManageSpeciesTest(unittest.TestCase):
    def setUp(self):
        self.site = SiteServer()

    def tearDown(self):
        self.site.stop()

    def test_create_species(self):
        response = self.site.request("POST", "/species/new", VALID_FORM)
        self.assertEqual(response.status, 303)
        location = response.headers["Location"]
        self.assertRegex(location, r"^/species/\d+$")

        detail = self.site.request("GET", location)
        self.assertEqual(detail.status, 200)
        self.assertIn("Testus examplea", detail.body)
        self.assertIn("Added during the end-to-end test.", detail.body)
        self.assertEqual(result_count(self.site.request("GET", "/").body), 13)

    def test_validate_species_input(self):
        empty = self.site.request(
            "POST", "/species/new", dict(VALID_FORM, scientific_name="", common_name="", habitat="")
        )
        self.assertEqual(empty.status, 200)
        self.assertIn("Scientific name is required.", empty.body)
        self.assertIn("Common name is required.", empty.body)
        self.assertIn("Habitat is required.", empty.body)

        duplicate = self.site.request(
            "POST", "/species/new", dict(VALID_FORM, scientific_name="canis LUPUS ")
        )
        self.assertIn("Scientific name already exists.", duplicate.body)

        lifespan = self.site.request("POST", "/species/new", dict(VALID_FORM, lifespan_years="0"))
        self.assertIn("Lifespan must be a whole number from 1 to 500.", lifespan.body)

        mass = self.site.request("POST", "/species/new", dict(VALID_FORM, body_mass_kg="0"))
        self.assertIn("Body mass must be a number greater than 0 and at most 200000.", mass.body)

        # 入力値は画面に残り、データは増えていない
        self.assertIn('value="Example animal"', lifespan.body)
        self.assertEqual(result_count(self.site.request("GET", "/").body), 12)

    def test_update_species(self):
        form_page = self.site.request("GET", "/species/1/edit")
        self.assertEqual(form_page.status, 200)
        self.assertIn('value="Gray wolf"', form_page.body)

        response = self.site.request(
            "POST",
            "/species/1/edit",
            dict(VALID_FORM, scientific_name="Canis lupus", common_name="Gray wolf",
                 taxonomic_class="Mammals", habitat="Forest", diet="Carnivore",
                 conservation_status="Least Concern", lifespan_years="7", body_mass_kg="40",
                 description="Updated description text."),
        )
        self.assertEqual(response.status, 303)
        self.assertEqual(response.headers["Location"], "/species/1")
        self.assertIn("Updated description text.", self.site.request("GET", "/species/1").body)

    def test_delete_species(self):
        response = self.site.request("POST", "/species/2/delete")
        self.assertEqual(response.status, 303)
        self.assertEqual(response.headers["Location"], "/")
        self.assertEqual(self.site.request("GET", "/species/2").status, 404)
        self.assertEqual(result_count(self.site.request("GET", "/").body), 11)


if __name__ == "__main__":
    unittest.main()
