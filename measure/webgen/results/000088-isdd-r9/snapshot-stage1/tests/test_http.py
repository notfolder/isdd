"""Integration tests: start the real server process and use HTTP only."""

import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request

import _paths  # noqa: F401
from _paths import PROJECT_ROOT

SERVER = os.path.join(PROJECT_ROOT, "src", "server.py")


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


class ServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.port = free_port()
        env = dict(os.environ, PORT=str(cls.port), DATA_DIR=cls.tmp.name)
        cls.proc = subprocess.Popen([sys.executable, SERVER], env=env,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cls.base = "http://127.0.0.1:%d" % cls.port
        cls._wait_until_ready()

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()  # only the server started by this test class
        cls.proc.wait(timeout=10)
        cls.tmp.cleanup()

    @classmethod
    def _wait_until_ready(cls):
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                urllib.request.urlopen(cls.base + "/", timeout=2).read()
                return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("server did not start")

    def get(self, path):
        try:
            response = OPENER.open(self.base + path, timeout=5)
            return response.status, response.headers, response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            return error.code, error.headers, error.read().decode("utf-8")

    def post(self, path, data):
        body = urllib.parse.urlencode(data).encode("utf-8")
        request = urllib.request.Request(self.base + path, data=body, method="POST",
                                         headers={"Content-Type": "application/x-www-form-urlencoded"})
        try:
            response = OPENER.open(request, timeout=5)
            return response.status, response.headers, response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            return error.code, error.headers, error.read().decode("utf-8")

    def form(self, **overrides):
        data = {
            "scientific_name": "Vulpes lagopus", "common_name": "Arctic fox", "class_name": "Mammalia",
            "family": "Canidae", "habitat": "Terrestrial", "diet": "Carnivore",
            "conservation_status": "LC", "average_lifespan_years": "", "average_adult_mass_kg": "",
            "description": "",
        }
        data.update(overrides)
        return data

    def test_home_and_list_are_served(self):
        status, _, body = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn("Species Database", body)
        status, _, body = self.get("/species")
        self.assertEqual(status, 200)
        self.assertIn("Showing 12 of 12 species", body)

    def test_filter_and_search_by_query_string(self):
        _, _, body = self.get("/species?class_name=Aves&habitat=Forest")
        self.assertIn("Showing 1 of 12 species", body)
        _, _, body = self.get("/species?q=zzzz")
        self.assertIn("No species match your search.", body)

    def test_create_redirects_to_detail_then_delete_redirects_to_list(self):
        status, headers, _ = self.post("/species/new", self.form())
        self.assertEqual(status, 303)
        location = headers["Location"]
        self.assertTrue(location.startswith("/species/"))
        status, _, body = self.get(location)
        self.assertEqual(status, 200)
        self.assertIn("Species saved.", body)
        self.assertIn("Arctic fox", body)

        species_id = location.split("?")[0].rsplit("/", 1)[1]
        status, headers, _ = self.post("/species/%s/delete" % species_id, {})
        self.assertEqual(status, 303)
        self.assertEqual(headers["Location"], "/species?deleted=1")
        _, _, body = self.get(headers["Location"])
        self.assertIn("Species deleted.", body)

    def test_invalid_form_is_shown_again_with_errors(self):
        status, _, body = self.post("/species/new", self.form(scientific_name="", average_lifespan_years="0"))
        self.assertEqual(status, 200)
        self.assertIn("Scientific name is required", body)
        self.assertIn("Average lifespan must be a whole number from 1 to 300.", body)

    def test_duplicate_scientific_name_is_rejected(self):
        status, _, body = self.post("/species/new", self.form(scientific_name="PANTHERA LEO"))
        self.assertEqual(status, 200)
        self.assertIn("This scientific name is already registered.", body)

    def test_edit_keeps_own_scientific_name_and_saves(self):
        _, _, body = self.get("/species?q=lion")
        self.assertIn("Lion", body)
        status, headers, _ = self.post("/species/1/edit", self.form(
            scientific_name="Panthera leo", common_name="Lion", class_name="Mammalia", family="Felidae",
            habitat="Grassland", diet="Carnivore", conservation_status="VU", description="Edited."))
        self.assertEqual(status, 303)
        self.assertEqual(headers["Location"], "/species/1?saved=1")
        _, _, body = self.get("/species/1")
        self.assertIn("Edited.", body)

    def test_unknown_species_and_paths_are_not_found(self):
        status, _, body = self.get("/species/99999")
        self.assertEqual(status, 404)
        self.assertIn("Species not found.", body)
        status, _, _ = self.get("/no/such/page")
        self.assertEqual(status, 404)
        status, _, _ = self.post("/species/99999/delete", {})
        self.assertEqual(status, 404)

    def test_stylesheet_is_served_with_linen_and_maroon_colors(self):
        status, headers, body = self.get("/static/style.css")
        self.assertEqual(status, 200)
        self.assertIn("text/css", headers["Content-Type"])
        self.assertIn("#FAF0E6", body)
        self.assertIn("#800000", body)

    def test_missing_static_file_is_not_found(self):
        status, _, _ = self.get("/static/../server.py")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
