"""Unit tests for HTML generation (src/views.py)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import views  # noqa: E402


class ViewsTest(unittest.TestCase):
    def test_layout_uses_light_yellow_background_and_dark_slate_gray_components(self):
        html = views.render_layout("Test", "<p>x</p>")
        self.assertIn("background: #FFFFE0", html)
        self.assertIn("#2F4F4F", html)
        self.assertNotIn("#000080", html)
        self.assertNotIn("background: #ffffff", html.lower())
        self.assertIn('href="/"', html)
        self.assertIn('href="/results"', html)
        self.assertIn(">Surveys<", html)
        self.assertNotIn("poll", html.lower())
        self.assertIn(">Results<", html)

    def test_user_text_is_escaped(self):
        poll = {"id": 1, "question": "<script>alert(1)</script>", "option_count": 1, "total_votes": 0}
        html = views.render_poll_list([poll])
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_vote_page_shows_error_message(self):
        html = views.render_vote_page({"id": 1, "question": "Q"},
                                      [{"id": 5, "text": "A"}], error="Please select an option.")
        self.assertIn("Please select an option.", html)
        self.assertIn('name="option_id" value="5"', html)

    def test_results_page_shows_notice_after_voting(self):
        result = {"poll": {"id": 1, "question": "Q"}, "total": 2,
                  "options": [{"id": 1, "text": "A", "votes": 2, "percent": 100.0}]}
        self.assertIn("Your vote has been recorded.", views.render_poll_results(result, notice=True))
        self.assertNotIn("Your vote has been recorded.", views.render_poll_results(result))
        self.assertIn("100.0%", views.render_poll_results(result))

    def test_vote_page_disables_controls_when_already_voted(self):
        html = views.render_vote_page({"id": 1, "question": "Q"},
                                      [{"id": 5, "text": "A"}], already_voted=True)
        self.assertIn("You have already voted.", html)
        self.assertIn('value="5" disabled>', html)
        self.assertIn('type="submit" disabled>', html)
        self.assertIn('href="/surveys/1/results"', html)

    def test_vote_page_keeps_controls_enabled_when_not_voted(self):
        html = views.render_vote_page({"id": 1, "question": "Q"}, [{"id": 5, "text": "A"}])
        body = html.split("<body>")[1]
        self.assertNotIn("You have already voted.", body)
        self.assertNotIn("disabled", body)

    def test_empty_poll_list_message(self):
        self.assertIn("No surveys available.", views.render_poll_list([]))


if __name__ == "__main__":
    unittest.main()
