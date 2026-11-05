"""Integration tests: the HTTP layer against a real server on a temporary database."""

import os
import tempfile
import threading
import unittest
from urllib import error, parse, request

from web.server import make_server, prepare_store


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.store = prepare_store(cls.tmp.name)
        cls.server = make_server(0, cls.store)
        cls.base = "http://127.0.0.1:%d" % cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp.cleanup()

    def get(self, path):
        try:
            with request.urlopen(self.base + path) as resp:
                return resp.status, resp.headers, resp.read().decode("utf-8")
        except error.HTTPError as err:
            return err.code, err.headers, err.read().decode("utf-8")

    def post(self, path, fields):
        data = parse.urlencode(fields).encode("utf-8")
        req = request.Request(self.base + path, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        opener = request.build_opener(_NoRedirect)
        try:
            with opener.open(req) as resp:
                return resp.status, resp.headers, resp.read().decode("utf-8")
        except error.HTTPError as err:
            return err.code, err.headers, err.read().decode("utf-8")

    def test_home_lists_three_features(self):
        status, _, html = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn("<h1>Home</h1>", html)
        self.assertIn('href="/barbers"', html)
        self.assertIn('href="/services"', html)
        self.assertIn('href="/notify"', html)

    def test_sample_data_visible(self):
        self.assertIn("Maria Lopez", self.get("/barbers")[2])
        self.assertIn("Classic haircut", self.get("/services")[2])

    def test_add_barber_redirects_and_shows_row(self):
        status, headers, _ = self.post("/barbers", {"name": "Test Barber", "specialty": "Beard"})
        self.assertEqual(status, 303)
        self.assertEqual(headers["Location"], "/barbers")
        self.assertIn("Test Barber", self.get("/barbers")[2])

    def test_invalid_barber_shows_errors_and_keeps_input(self):
        status, _, html = self.post("/barbers", {"name": "", "specialty": "Keep me"})
        self.assertEqual(status, 400)
        self.assertIn("Name is required.", html)
        self.assertIn('value="Keep me"', html)

    def test_add_service_rejects_negative_price(self):
        status, _, html = self.post("/services", {"name": "Bad", "price": "-1", "duration_min": "20"})
        self.assertEqual(status, 400)
        self.assertIn("Price must be between 0 and 10000.", html)

    def test_notify_returns_one_link_per_number(self):
        status, _, html = self.post("/notify", {"phones": "+15550101\n+81905555 0103", "message": "See you & relax"})
        self.assertEqual(status, 200)
        self.assertIn("https://wa.me/15550101?text=See%20you%20%26%20relax", html)
        self.assertIn("https://wa.me/819055550103?text=", html)
        self.assertEqual(html.count("Open in WhatsApp"), 2)

    def test_notify_invalid_number_creates_no_links(self):
        status, _, html = self.post("/notify", {"phones": "+15550101\nabc", "message": "Hi"})
        self.assertEqual(status, 400)
        self.assertNotIn("wa.me", html)

    def test_static_css_and_snow_and_dim_gray(self):
        status, headers, css = self.get("/static/style.css")
        self.assertEqual(status, 200)
        self.assertIn("text/css", headers["Content-Type"])
        self.assertIn("#696969", css)
        self.assertIn("reduced-motion", css)
        html = self.get("/")[2]
        self.assertIn('class="snowflake"', html)

    def test_unknown_path_is_404_in_english(self):
        status, _, html = self.get("/nope")
        self.assertEqual(status, 404)
        self.assertIn("The page was not found.", html)

    def test_html_is_escaped(self):
        self.post("/barbers", {"name": "<b>x</b>"})
        self.assertNotIn("<b>x</b>", self.get("/barbers")[2])
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", self.get("/barbers")[2])


class _NoRedirect(request.HTTPRedirectHandler):
    """Do not follow redirects so the 303 can be checked."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


if __name__ == "__main__":
    unittest.main()
