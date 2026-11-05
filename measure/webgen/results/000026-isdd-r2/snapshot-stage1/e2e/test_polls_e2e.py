"""End-to-end scenarios for the polls website.

A real server (src/server.py) is started as a child process on a free port with a temporary
DATA_DIR. Each test drives it over HTTP with its own cookie jar, the way a browser does.
"""
import http.cookiejar
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVER_SCRIPT = PROJECT_ROOT / "src" / "server.py"

_server = None
_base_url = None
_data_dir = None


def _free_port():
    """Return a TCP port on 127.0.0.1 that is currently free."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def setUpModule():
    """Start the server on a free port with an empty temporary DATA_DIR."""
    global _server, _base_url, _data_dir
    _data_dir = tempfile.TemporaryDirectory()
    port = _free_port()
    env = dict(os.environ, PORT=str(port), DATA_DIR=_data_dir.name)
    _server = subprocess.Popen([sys.executable, str(SERVER_SCRIPT)], env=env, cwd=str(PROJECT_ROOT),
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _base_url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            urllib.request.urlopen(_base_url + "/polls", timeout=2).read()
            return
        except OSError:
            time.sleep(0.2)
    tearDownModule()
    raise RuntimeError("the polls server did not start in time")


def tearDownModule():
    """Stop the server process started by setUpModule (by its own handle) and remove the temporary DATA_DIR."""
    global _server, _data_dir
    if _server is not None and _server.poll() is None:
        _server.terminate()
        try:
            _server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _server.kill()
            _server.wait(timeout=10)
    _server = None
    if _data_dir is not None:
        _data_dir.cleanup()
        _data_dir = None


class Browser:
    """A minimal browser: follows redirects, keeps cookies, and reports status, final URL and body."""

    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def _request(self, method, path, form=None):
        body = urllib.parse.urlencode(form).encode("utf-8") if form is not None else None
        request = urllib.request.Request(_base_url + path, data=body, method=method)
        try:
            with self.opener.open(request, timeout=10) as response:
                return response.status, response.geturl(), response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            return error.code, error.geturl(), error.read().decode("utf-8")

    def get(self, path):
        return self._request("GET", path)

    def post(self, path, form):
        return self._request("POST", path, form)

    def has_voter_cookie(self):
        return any(cookie.name == "voter_token" for cookie in self.jar)


def option_ids(html):
    """Return the option ids offered by a poll detail page, in page order."""
    return re.findall(r'name="option_id" value="(\d+)"', html)


class PollsEndToEndTest(unittest.TestCase):
    def test_browse_polls_flow(self):
        """DS-TS-BROWSE-POLLS-E2E: the poll list shows the sample polls and a poll shows its options."""
        browser = Browser()
        status, final_url, body = browser.get("/")
        self.assertEqual(status, 200)
        self.assertTrue(final_url.endswith("/polls"))
        self.assertEqual(body.count('class="card"'), 3)

        status, _, body = browser.get("/polls/1")
        self.assertEqual(status, 200)
        self.assertIn("Which programming language do you prefer?", body)
        self.assertGreaterEqual(len(option_ids(body)), 3)
        self.assertIn("Vote", body)

    def test_cast_vote_flow(self):
        """DS-TS-CAST-VOTE-E2E: a vote is recorded and the results page shows it."""
        browser = Browser()
        _, _, body = browser.get("/polls/2")
        choice = option_ids(body)[0]
        before = re.search(r"Total votes: (\d+)", browser.get("/polls/2/results")[2])
        status, final_url, body = browser.post("/polls/2/vote", {"option_id": choice})
        self.assertEqual(status, 200)
        self.assertIn("/polls/2/results", final_url)
        self.assertIn("Total votes:", body)
        after = re.search(r"Total votes: (\d+)", body)
        self.assertEqual(int(after.group(1)), int(before.group(1)) + 1)
        self.assertTrue(browser.has_voter_cookie())

    def test_one_vote_rule(self):
        """DS-TS-ONE-VOTE-RULE-E2E: the same browser cannot vote twice in one poll."""
        browser = Browser()
        _, _, body = browser.get("/polls/3")
        choices = option_ids(body)
        first_status, _, _ = browser.post("/polls/3/vote", {"option_id": choices[0]})
        self.assertEqual(first_status, 200)
        before = re.search(r"Total votes: (\d+)", browser.get("/polls/3/results")[2]).group(1)

        status, _, body = browser.post("/polls/3/vote", {"option_id": choices[1]})
        self.assertEqual(status, 409)
        self.assertIn("You have already voted in this poll.", body)
        after = re.search(r"Total votes: (\d+)", browser.get("/polls/3/results")[2]).group(1)
        self.assertEqual(before, after)

    def test_validate_vote(self):
        """DS-TS-VALIDATE-VOTE-E2E: an empty or invalid selection is refused and nothing is stored."""
        browser = Browser()
        _, _, body = browser.get("/polls/1")
        status, _, body_empty = browser.post("/polls/1/vote", {})
        self.assertEqual(status, 400)
        self.assertIn("Please select an option before voting.", body_empty)

        other_poll_option = option_ids(browser.get("/polls/2")[2])[0]
        status, _, body_invalid = browser.post("/polls/1/vote", {"option_id": other_poll_option})
        self.assertEqual(status, 400)
        self.assertIn("The selected option is not valid for this poll.", body_invalid)

        _, _, body_after = browser.get("/polls/1")
        self.assertIn('<button type="submit"', body_after)
        self.assertNotIn("You have already voted", body_after)

    def test_view_results(self):
        """DS-TS-VIEW-RESULTS-E2E: the results page lists each option with its count and one-decimal share."""
        browser = Browser()
        status, _, body = browser.get("/polls/1/results")
        self.assertEqual(status, 200)
        self.assertIn("Total votes:", body)
        self.assertRegex(body, r"\d+\.\d%")
        self.assertIn("Python", body)
        self.assertIn("JavaScript", body)

    def test_results_list(self):
        """DS-TS-RESULTS-LIST-E2E: the results list links to each poll's results."""
        browser = Browser()
        status, _, body = browser.get("/results")
        self.assertEqual(status, 200)
        for poll_id in (1, 2, 3):
            self.assertIn(f'href="/polls/{poll_id}/results"', body)
        status, _, body = browser.get("/polls/3/results")
        self.assertEqual(status, 200)
        self.assertIn("Total votes:", body)

    def test_navigation(self):
        """DS-TS-NAVIGATION-E2E: the navigation moves between the main screens and the page styles are applied."""
        browser = Browser()
        status, final_url, body = browser.get("/")
        self.assertTrue(final_url.endswith("/polls"))
        self.assertIn('href="/results"', body)
        self.assertIn('href="/polls"', body)

        _, _, body = browser.get("/results")
        self.assertIn("Results", body)
        _, _, body = browser.get("/polls")
        self.assertIn("Polls", body)

        status, _, css = browser.get("/static/style.css")
        self.assertEqual(status, 200)
        self.assertIn("#000080", css)
        self.assertIn("#ffffff", css)


if __name__ == "__main__":
    unittest.main()
