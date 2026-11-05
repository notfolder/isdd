import unittest

import _paths  # noqa: F401
import views


def species(**overrides):
    item = {
        "id": 7,
        "scientific_name": "Panthera leo",
        "common_name": "Lion",
        "class_name": "Mammalia",
        "family": "Felidae",
        "habitat": "Grassland",
        "diet": "Carnivore",
        "conservation_status": "VU",
        "average_lifespan_years": 14,
        "average_adult_mass_kg": 190.0,
        "description": "Large cat.",
    }
    item.update(overrides)
    return item


class ViewsTest(unittest.TestCase):
    def test_layout_has_navigation_and_stylesheet(self):
        html = views.render_layout("Home", "<p>x</p>")
        for label in ("Home", "Browse species", "Add species"):
            self.assertIn(">%s</a>" % label, html)
        self.assertIn('href="/static/style.css"', html)
        self.assertIn('lang="en"', html)

    def test_user_input_is_escaped_on_detail_screen(self):
        html = views.render_species_detail(species(description="<b>bold</b>"), "")
        self.assertIn("&lt;b&gt;bold&lt;/b&gt;", html)
        self.assertNotIn("<b>bold</b>", html)

    def test_detail_back_link_keeps_query(self):
        html = views.render_species_detail(species(), "q=lion&class_name=Mammalia")
        self.assertIn('href="/species?q=lion&amp;class_name=Mammalia"', html)

    def test_detail_shows_dash_for_empty_optional_values(self):
        html = views.render_species_detail(species(family="", average_lifespan_years=None,
                                                   average_adult_mass_kg=None, description=""), "")
        self.assertIn("&mdash;", html)

    def test_list_shows_empty_message_and_count(self):
        html = views.render_species_list([], "zzzz", {}, 12, "q=zzzz")
        self.assertIn("No species match your search.", html)
        self.assertIn("Showing 0 of 12 species", html)

    def test_list_links_detail_with_query(self):
        html = views.render_species_list([species()], "", {}, 1, "class_name=Mammalia")
        self.assertIn('href="/species/7?class_name=Mammalia"', html)

    def test_form_shows_errors_and_keeps_values(self):
        html = views.render_species_form({"scientific_name": "Bad<tag>"}, {"scientific_name": "Scientific name is required."},
                                         "/species/new", "Add species", "/species")
        self.assertIn("Bad&lt;tag&gt;", html)
        self.assertIn('<p class="field-error">Scientific name is required.</p>', html)

    def test_not_found_message(self):
        html = views.render_not_found()
        self.assertIn("Species not found.", html)
        self.assertIn("Back to species list", html)

    def test_notice_is_shown(self):
        html = views.render_species_detail(species(), "", notice="Species saved.")
        self.assertIn('<p class="notice" role="status">Species saved.</p>', html)


if __name__ == "__main__":
    unittest.main()
