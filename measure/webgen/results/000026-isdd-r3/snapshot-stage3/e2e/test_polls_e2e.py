"""End-to-end tests: start the real server in a subprocess and operate it over HTTP.

The server gets an empty temporary DATA_DIR and a free port. Only the process
started here is stopped at the end.
"""

import http.cookiejar
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
APP = PROJECT_ROOT / "src" / "app.py"
SAMPLE_QUESTIONS = [
    "What is your favourite programming language?",
    "Which season do you like best?",
    "Where should we hold the team lunch?",
]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Return 302 responses as they are, so the test can check the redirect target."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class PollsE2ETest(unittest.TestCase):
    base_url = ""
    _proc = None
    _tmp = None

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        port = _free_port()
        env = {"PORT": str(port), "DATA_DIR": cls._tmp.name, "PATH": "/usr/bin:/bin"}
        cls._proc = subprocess.Popen(
            [sys.executable, str(APP)], env=env, cwd=str(PROJECT_ROOT),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        cls.base_url = f"http://127.0.0.1:{port}"
        deadline = time.time() + 15
        while True:
            try:
                urllib.request.urlopen(cls.base_url + "/", timeout=1).read()
                break
            except (urllib.error.URLError, ConnectionError, OSError):
                if cls._proc.poll() is not None or time.time() > deadline:
                    raise RuntimeError("server did not start")
                time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        if cls._proc is not None and cls._proc.poll() is None:
            cls._proc.terminate()
            try:
                cls._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls._proc.kill()
                cls._proc.wait()
        if cls._tmp is not None:
            cls._tmp.cleanup()

    def setUp(self):
        """Every test is a new browser: it has its own cookie jar and no vote yet."""
        self._jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(
            _NoRedirect, urllib.request.HTTPCookieProcessor(self._jar))

    # helpers -----------------------------------------------------------

    def _get(self, path):
        """Return (status, body) for a GET request. HTTP error statuses are returned too."""
        try:
            with self._opener.open(self.base_url + path, timeout=5) as response:
                return response.status, response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            return error.code, error.read().decode("utf-8")

    def _post(self, path, fields=None):
        """Return (status, location, body) for a POST request with form fields."""
        data = urllib.parse.urlencode(fields or {}).encode("utf-8")
        request = urllib.request.Request(self.base_url + path, data=data, method="POST")
        try:
            with self._opener.open(request, timeout=5) as response:
                return response.status, response.headers.get("Location"), response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            return error.code, error.headers.get("Location"), error.read().decode("utf-8")

    def _poll_id_for(self, question):
        status, body = self._get("/")
        self.assertEqual(status, 200)
        match = re.search(r'<h2>' + re.escape(question) + r'</h2>.*?href="/surveys/(\d+)"', body, re.S)
        self.assertIsNotNone(match, f"poll not listed: {question}")
        return int(match.group(1))

    def _option_id(self, poll_id, text):
        status, body = self._get(f"/surveys/{poll_id}")
        self.assertEqual(status, 200)
        match = re.search(r'name="option_id" value="(\d+)"> ' + re.escape(text) + r"</label>", body)
        self.assertIsNotNone(match, f"option not shown: {text}")
        return int(match.group(1))

    def _total_votes(self, poll_id):
        status, body = self._get(f"/surveys/{poll_id}/results")
        self.assertEqual(status, 200)
        return int(re.search(r"Total votes: (\d+)", body).group(1))

    # tests (the names are referenced from the trace map) ----------------

    def test_anonymous_access(self):
        """every screen opens without login."""
        poll_id = self._poll_id_for(SAMPLE_QUESTIONS[0])
        for path in ["/", f"/surveys/{poll_id}", f"/surveys/{poll_id}/results", "/results"]:
            status, _ = self._get(path)
            self.assertEqual(status, 200, path)

    def test_browse_polls(self):
        """the survey list shows the sample surveys and the navigation menu."""
        status, body = self._get("/")
        self.assertEqual(status, 200)
        for question in SAMPLE_QUESTIONS:
            self.assertIn(question, body)
        self.assertIn('href="/"', body)
        self.assertIn('href="/results"', body)
        self.assertIn(">Surveys<", body)
        self.assertIn(">Results<", body)

    def test_open_unknown_poll(self):
        """an unknown survey shows a 404 page."""
        status, body = self._get("/surveys/9999")
        self.assertEqual(status, 404)
        self.assertIn("Survey not found.", body)

    def test_reject_empty_vote(self):
        """submitting without a choice records nothing and shows an error."""
        poll_id = self._poll_id_for(SAMPLE_QUESTIONS[1])
        before = self._total_votes(poll_id)
        status, location, body = self._post(f"/surveys/{poll_id}/vote", {})
        self.assertEqual(status, 200)
        self.assertIsNone(location)
        self.assertIn("Please select an option.", body)
        self.assertEqual(self._total_votes(poll_id), before)

    def test_seed_sample_data(self):
        """the empty data directory starts with sample polls and votes."""
        status, body = self._get("/results")
        self.assertEqual(status, 200)
        for question in SAMPLE_QUESTIONS:
            self.assertIn(question, body)
        self.assertGreater(int(re.search(r"Total votes: (\d+)", body).group(1)), 0)

    def test_view_all_results(self):
        """the overview lists every poll with counts and shares."""
        status, body = self._get("/results")
        self.assertEqual(status, 200)
        for question in SAMPLE_QUESTIONS:
            self.assertIn(question, body)
        self.assertIn("%", body)

    def test_vote_for_option(self):
        """a chosen option gets one vote and the result page shows it."""
        poll_id = self._poll_id_for(SAMPLE_QUESTIONS[0])
        option_id = self._option_id(poll_id, "Go")
        before_total = self._total_votes(poll_id)
        status, location, _ = self._post(f"/surveys/{poll_id}/vote", {"option_id": option_id})
        self.assertEqual(status, 302)
        self.assertEqual(location, f"/surveys/{poll_id}/results?voted=1")
        status, body = self._get(location)
        self.assertEqual(status, 200)
        self.assertIn("Your vote has been recorded.", body)
        self.assertEqual(int(re.search(r"Total votes: (\d+)", body).group(1)), before_total + 1)
        go_votes = int(re.search(r"<td>Go</td><td>(\d+)</td>", body).group(1))
        self.assertGreater(go_votes, 0)

    def test_one_vote_per_poll_per_browser(self):
        """a second vote from the same browser is not counted, by the form or a direct POST."""
        poll_id = self._poll_id_for(SAMPLE_QUESTIONS[2])
        option_id = self._option_id(poll_id, "Mexican")
        status, location, _ = self._post(f"/surveys/{poll_id}/vote", {"option_id": option_id})
        self.assertEqual(status, 302)
        after_first = self._total_votes(poll_id)
        status, body = self._get(f"/surveys/{poll_id}")
        self.assertEqual(status, 200)
        self.assertIn("You have already voted.", body)
        self.assertIn('type="submit" disabled>', body)
        status, location, body = self._post(f"/surveys/{poll_id}/vote", {"option_id": option_id})
        self.assertEqual(status, 200)
        self.assertIsNone(location)
        self.assertIn("You have already voted.", body)
        self.assertEqual(self._total_votes(poll_id), after_first)

    def test_survey_terminology(self):
        """no user-visible page or URL contains the word poll; the old /polls URL is gone."""
        poll_id = self._poll_id_for(SAMPLE_QUESTIONS[0])
        for path in ["/", f"/surveys/{poll_id}", f"/surveys/{poll_id}/results", "/results"]:
            status, body = self._get(path)
            self.assertEqual(status, 200, path)
            self.assertIsNone(re.search(r"poll", body, re.I), path)
        status, _ = self._get(f"/polls/{poll_id}")
        self.assertEqual(status, 404)

    def test_theme_colors(self):
        """every screen uses the light yellow background and dark slate gray components, no navy or white background."""
        poll_id = self._poll_id_for(SAMPLE_QUESTIONS[0])
        for path in ["/", f"/surveys/{poll_id}", f"/surveys/{poll_id}/results", "/results"]:
            status, body = self._get(path)
            self.assertEqual(status, 200, path)
            self.assertIn("background: #FFFFE0", body, path)
            self.assertIn("#2F4F4F", body, path)
            self.assertNotIn("#000080", body, path)
            self.assertNotIn("background: #ffffff", body.lower(), path)


if __name__ == "__main__":
    unittest.main()
