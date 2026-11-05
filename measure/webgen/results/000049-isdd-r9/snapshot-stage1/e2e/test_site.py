"""End-to-end tests: start the real site (run.sh's server module) and check it over HTTP.

Each test class starts its own server process on a free port with its own DATA_DIR,
and stops only that process when the class finishes.
"""

import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from html.parser import HTMLParser
from urllib import error, parse, request

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def free_port():
    """Return a TCP port that is free on 127.0.0.1 right now."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class SiteServer:
    """A site server started as a child process of the test."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.port = free_port()
        self.base = "http://127.0.0.1:%d" % self.port
        self.proc = None

    def start(self):
        env = dict(os.environ)
        env.update({"PORT": str(self.port), "DATA_DIR": self.data_dir, "PYTHONPATH": os.path.join(PROJECT_ROOT, "src")})
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "web.server"],
            cwd=PROJECT_ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        deadline = time.time() + 15
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError("server exited: %s" % self.proc.stderr.read().decode("utf-8", "replace"))
            try:
                with request.urlopen(self.base + "/", timeout=1):
                    return self
            except (error.URLError, OSError):
                time.sleep(0.1)
        raise RuntimeError("server did not start")

    def stop(self):
        """Stop the child process this test started (by its own handle, never by name)."""
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
        self.proc = None

    def get(self, path):
        try:
            with request.urlopen(self.base + path, timeout=10) as resp:
                return resp.status, dict(resp.headers), resp.read().decode("utf-8")
        except error.HTTPError as err:
            return err.code, dict(err.headers), err.read().decode("utf-8")

    def post(self, path, fields):
        data = parse.urlencode(fields).encode("utf-8")
        req = request.Request(self.base + path, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        opener = request.build_opener(NoRedirect)
        try:
            with opener.open(req, timeout=10) as resp:
                return resp.status, dict(resp.headers), resp.read().decode("utf-8")
        except error.HTTPError as err:
            return err.code, dict(err.headers), err.read().decode("utf-8")


class NoRedirect(request.HTTPRedirectHandler):
    """Return the 303 response itself instead of following it."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class PageParser(HTMLParser):
    """Collects the nav links, table cells, error items and link targets of a page."""

    def __init__(self):
        super().__init__()
        self.nav_links = []
        self.cells = []
        self.rows = []
        self.errors = []
        self.hrefs = []
        self.current_row = None
        self._in_nav = False
        self._in_cell = False
        self._in_error = False
        self._cell_text = ""
        self._error_text = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "nav":
            self._in_nav = True
        if tag == "a":
            if self._in_nav:
                self.nav_links.append(a.get("href"))
            if a.get("href"):
                self.hrefs.append(a["href"])
        if tag == "tr":
            self.current_row = []
        if tag in ("td", "th"):
            self._in_cell = True
            self._cell_text = ""
        if tag == "li" and "errors-item" not in (a.get("class") or ""):
            pass
        if a.get("class") == "errors":
            self._in_error = True
        if tag == "li" and self._in_error:
            self._error_text = ""

    def handle_endtag(self, tag):
        if tag == "nav":
            self._in_nav = False
        if tag in ("td", "th"):
            self._in_cell = False
            if self.current_row is not None:
                self.current_row.append(self._cell_text.strip())
        if tag == "tr" and self.current_row is not None:
            self.rows.append(self.current_row)
            self.current_row = None
        if tag == "li" and self._in_error:
            self.errors.append(self._error_text.strip())
        if tag == "div" and self._in_error:
            self._in_error = False

    def handle_data(self, data):
        if self._in_cell:
            self._cell_text += data
        if self._in_error:
            self._error_text += data


def parse_page(html):
    """Return a PageParser filled with the page's content."""
    parser = PageParser()
    parser.feed(html)
    return parser


class SampleSiteTests(unittest.TestCase):
    """Shared server with the sample data (DATA_DIR starts empty)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.server = SiteServer(cls.tmp.name).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        cls.tmp.cleanup()

    def test_navigate_from_home(self):
        status, _, home = self.server.get("/")
        self.assertEqual(status, 200)
        nav = parse_page(home).nav_links
        self.assertEqual(nav, ["/", "/barbers", "/services", "/notify"])
        for path in ("/barbers", "/services", "/notify"):
            status, _, html = self.server.get(path)
            self.assertEqual(status, 200, path)
            self.assertIn('aria-current="page"', html, path)
        self.assertIn("/barbers", parse_page(home).hrefs)
        self.assertIn("/services", parse_page(home).hrefs)
        self.assertIn("/notify", parse_page(home).hrefs)

    def test_browse_and_add_barber(self):
        status, headers, _ = self.server.post("/barbers", {"name": "E2E Barber", "specialty": "Beard", "phone": "+1 555 0177"})
        self.assertEqual(status, 303)
        self.assertEqual(headers.get("Location"), "/barbers")
        rows = data_rows(self.server.get("/barbers")[2])
        self.assertIn(["E2E Barber", "Beard", "+1 555 0177"], rows)
        self.assertIn("/barbers/new", self.server.get("/barbers")[2])

    def test_browse_and_add_service(self):
        status, headers, _ = self.server.post(
            "/services", {"name": "E2E Cut", "price": "12.50", "duration_min": "20", "description": "Quick"}
        )
        self.assertEqual(status, 303)
        self.assertEqual(headers.get("Location"), "/services")
        rows = data_rows(self.server.get("/services")[2])
        self.assertIn(["E2E Cut", "12.50", "20 min", "Quick"], rows)

    def test_send_whatsapp_links(self):
        status, _, html = self.server.post(
            "/notify",
            {"phones": "+1 555 0101\n+81 90 5555 0103", "message": "Your turn is at 10:00 & see you"},
        )
        self.assertEqual(status, 200)
        hrefs = [h for h in parse_page(html).hrefs if h.startswith("https://wa.me/")]
        self.assertEqual(len(hrefs), 2, hrefs)
        self.assertTrue(hrefs[0].startswith("https://wa.me/15550101?text="), hrefs[0])
        self.assertTrue(hrefs[1].startswith("https://wa.me/819055550103?text="), hrefs[1])
        self.assertEqual(parse.parse_qs(parse.urlsplit(hrefs[0]).query)["text"][0], "Your turn is at 10:00 & see you")

    def test_reject_invalid_entries(self):
        status, _, html = self.server.post("/barbers", {"name": "", "specialty": "Keep this"})
        self.assertEqual(status, 400)
        self.assertIn("Name is required.", parse_page(html).errors)
        self.assertIn('value="Keep this"', html)

        status, _, html = self.server.post("/services", {"name": "Bad", "price": "-1", "duration_min": "20"})
        self.assertEqual(status, 400)
        self.assertIn("Price must be between 0 and 10000.", parse_page(html).errors)

        status, _, html = self.server.post("/notify", {"phones": "+15550101\nabc", "message": "Hi"})
        self.assertEqual(status, 400)
        self.assertTrue(any("abc" in e for e in parse_page(html).errors))
        self.assertNotIn("wa.me", html)

        # nothing from the rejected forms was saved
        self.assertNotIn("Bad", self.server.get("/services")[2])
        self.assertNotIn("Keep this", self.server.get("/barbers")[2])

    def test_snow_and_gray_theme(self):
        status, _, html = self.server.get("/")
        self.assertEqual(status, 200)
        self.assertIn('class="snow"', html)
        self.assertGreaterEqual(html.count('class="snowflake"'), 10)
        self.assertIn('href="/static/style.css"', html)
        status, headers, css = self.server.get("/static/style.css")
        self.assertEqual(status, 200)
        self.assertIn("text/css", headers.get("Content-Type", ""))
        self.assertIn("--dim-gray: #696969", css)
        self.assertIn("pointer-events: none", css)
        self.assertIn("prefers-reduced-motion: reduce", css)


def data_rows(html):
    """Return the table body rows of a page (header row excluded)."""
    return [r for r in parse_page(html).rows if r and r[0] not in ("Name",)]


class EmptyDataDirTests(unittest.TestCase):
    """A fresh DATA_DIR gets sample data at first start, and the site works without it being edited."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.server = SiteServer(os.path.join(cls.tmp.name, "data")).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        cls.tmp.cleanup()

    def test_database_file_is_created_in_data_dir(self):
        self.assertTrue(os.path.exists(os.path.join(self.server.data_dir, "barbershop.db")))

    def test_start_with_sample_data(self):
        status, _, html = self.server.get("/barbers")
        self.assertEqual(status, 200)
        barbers = data_rows(html)
        self.assertEqual(len(barbers), 3, barbers)
        status, _, html = self.server.get("/services")
        self.assertEqual(status, 200)
        services = data_rows(html)
        self.assertEqual(len(services), 4, services)
        self.assertIn("Classic haircut", html)




if __name__ == "__main__":
    unittest.main()
