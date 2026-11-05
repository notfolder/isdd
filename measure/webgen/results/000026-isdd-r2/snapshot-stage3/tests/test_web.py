"""Integration tests for the HTTP routes, using the Flask test client and a temporary DATA_DIR."""
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import server  # noqa: E402
import voter  # noqa: E402


class WebRoutesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.app = server.create_app(self._tmp.name)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def tearDown(self):
        self._tmp.cleanup()

    def test_root_redirects_to_poll_list(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/surveys"))

    def test_survey_list_shows_sample_surveys_and_navigation(self):
        html = self.client.get("/surveys").get_data(as_text=True)
        self.assertIn("Which programming language do you prefer?", html)
        self.assertIn("Results", html)
        self.assertIn("Surveys", html)
        self.assertNotIn("poll", html.lower())

    def test_old_poll_addresses_redirect_to_surveys(self):
        response = self.client.get("/polls")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/surveys"))
        response = self.client.get("/polls/1/results")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/surveys/1/results"))
        self.assertEqual(self.client.get("/polls/1/results", follow_redirects=True).status_code, 200)

    def test_poll_detail_shows_radio_options(self):
        html = self.client.get("/surveys/1").get_data(as_text=True)
        self.assertIn('type="radio" name="option_id"', html)
        self.assertIn("Vote", html)

    def test_unknown_poll_returns_404(self):
        self.assertEqual(self.client.get("/surveys/999").status_code, 404)
        self.assertEqual(self.client.get("/surveys/999/results").status_code, 404)
        self.assertEqual(self.client.post("/surveys/999/vote", data={"option_id": "1"}).status_code, 404)

    def test_vote_success_sets_cookie_and_redirects_to_results(self):
        response = self.client.post("/surveys/1/vote", data={"option_id": self._first_option(1)})
        self.assertEqual(response.status_code, 303)
        self.assertIn("/surveys/1/results", response.headers["Location"])
        cookie = response.headers.get("Set-Cookie", "")
        self.assertIn(voter.COOKIE_NAME + "=", cookie)
        self.assertIn("HttpOnly", cookie)

    def test_second_vote_from_same_browser_is_refused(self):
        option = self._first_option(1)
        self.client.post("/surveys/1/vote", data={"option_id": option})
        response = self.client.post("/surveys/1/vote", data={"option_id": option})
        self.assertEqual(response.status_code, 409)
        self.assertIn("You have already voted in this survey.", response.get_data(as_text=True))

    def test_voted_poll_shows_disabled_controls_and_message(self):
        option = self._first_option(1)
        self.client.post("/surveys/1/vote", data={"option_id": option})
        html = self.client.get("/surveys/1").get_data(as_text=True)
        self.assertIn("You have already voted in this survey.", html)
        self.assertIn("<fieldset disabled>", html)
        radios = re.findall(r'<input type="radio"[^>]*>', html)
        self.assertGreaterEqual(len(radios), 2)
        self.assertTrue(all(" disabled" in radio for radio in radios))
        self.assertIn('<button type="submit" class="button" disabled>', html)

    def test_voted_browser_posting_without_selection_gets_disabled_form(self):
        self.client.post("/surveys/1/vote", data={"option_id": self._first_option(1)})
        response = self.client.post("/surveys/1/vote", data={})
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn("You have already voted in this survey.", html)
        self.assertIn("<fieldset disabled>", html)

    def test_unvoted_poll_keeps_controls_enabled(self):
        html = self.client.get("/surveys/2").get_data(as_text=True)
        self.assertIn("<fieldset>", html)
        self.assertNotIn("disabled", html)
        self.assertNotIn("You have already voted", html)

    def test_missing_selection_is_refused_with_message(self):
        response = self.client.post("/surveys/2/vote", data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Please select an option before voting.", response.get_data(as_text=True))

    def test_foreign_option_is_refused_with_message(self):
        foreign = self._first_option(2)
        response = self.client.post("/surveys/1/vote", data={"option_id": foreign})
        self.assertEqual(response.status_code, 400)
        self.assertIn("The selected option is not valid for this survey.", response.get_data(as_text=True))

    def test_results_page_shows_counts_and_percentages(self):
        html = self.client.get("/surveys/1/results").get_data(as_text=True)
        self.assertIn("Total votes: 11", html)
        self.assertIn("45.5%", html)

    def test_results_list_links_each_poll(self):
        html = self.client.get("/results").get_data(as_text=True)
        self.assertIn('href="/surveys/1/results"', html)
        self.assertIn('href="/surveys/3/results"', html)

    def _first_option(self, poll_id):
        html = self.client.get(f"/surveys/{poll_id}").get_data(as_text=True)
        marker = 'name="option_id" value="'
        start = html.index(marker) + len(marker)
        return html[start : html.index('"', start)]


if __name__ == "__main__":
    unittest.main()
