"""End-to-end tests: a real browser (Playwright, Chromium) drives the species database.

Each test starts its own server process with a fresh DATA_DIR and stops only that process.
Run with: .venv/bin/python scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml
"""

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
from concurrent.futures import ThreadPoolExecutor

from playwright.sync_api import expect, sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(PROJECT_ROOT, "src", "server.py")
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from repository import SpeciesRepository  # noqa: E402

LINEN_RGB = "rgb(250, 240, 230)"
MAROON_RGB = "rgb(128, 0, 0)"
JAPANESE_CHARS = re.compile(r"[぀-ヿ㐀-䶿一-鿿]")
SAMPLE_NAMES_BY_NAME = [
    "Asian elephant", "Blue whale", "Common carp", "Emperor penguin", "Giant panda", "Green sea turtle",
    "House sparrow", "Japanese bush warbler", "Japanese giant salamander", "Japanese macaque", "Lion",
    "Seven-spot ladybird",
]


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class AppServer:
    """A server process started by this test. Only this process is stopped."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.port = free_port()
        self.proc = None

    @property
    def url(self):
        return "http://127.0.0.1:%d" % self.port

    def start(self):
        env = dict(os.environ, PORT=str(self.port), DATA_DIR=self.data_dir)
        self.proc = subprocess.Popen([sys.executable, SERVER], env=env,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                urllib.request.urlopen(self.url + "/", timeout=2).read()
                return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("server did not start")

    def stop(self):
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
            self.proc.wait(timeout=10)


class SpeciesE2ETest(unittest.TestCase):
    playwright = None
    browser = None

    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.server = AppServer(self.tmp.name)
        self.server.start()
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.page.set_default_timeout(10000)

    def tearDown(self):
        self.context.close()
        self.server.stop()
        self.tmp.cleanup()

    def open(self, path=""):
        self.page.goto(self.server.url + path)

    def rows(self):
        return self.page.locator("tbody tr")

    def fill_new_species(self, **overrides):
        values = {
            "Scientific name": "Vulpes lagopus",
            "Common name": "Arctic fox",
            "Family": "Canidae",
            "Average lifespan (years)": "10",
            "Average adult mass (kg)": "3.5",
            "Description": "Small arctic fox.",
        }
        values.update(overrides)
        for label, value in values.items():
            self.page.get_by_label(label, exact=True).fill(value)
        self.page.get_by_label("Class", exact=True).select_option("Mammalia")
        self.page.get_by_label("Habitat", exact=True).select_option("Terrestrial")
        self.page.get_by_label("Diet", exact=True).select_option("Carnivore")
        self.page.get_by_label("Conservation status", exact=True).select_option("LC")

    def test_open_home_and_menu(self):
        self.open("/")
        expect(self.page.get_by_role("heading", name="Species Database", level=1)).to_be_visible()
        self.assertEqual(self.page.get_by_test_id("total-species").inner_text(), "12")
        nav = self.page.get_by_role("navigation", name="Main navigation")
        nav.get_by_role("link", name="Browse species").click()
        expect(self.page.get_by_role("heading", name="Browse species", level=1)).to_be_visible()
        nav.get_by_role("link", name="Add species").click()
        expect(self.page.get_by_role("heading", name="Add species", level=1)).to_be_visible()
        nav.get_by_role("link", name="Home").click()
        expect(self.page.get_by_test_id("threatened-species")).to_have_text("6")

    def test_sample_data_on_first_run(self):
        self.open("/species")
        expect(self.page.get_by_text("Showing 12 of 12 species")).to_be_visible()
        self.assertEqual(self.rows().count(), 12)
        self.assertEqual(self.rows().first.locator("a").inner_text(), "Asian elephant")

    def test_browse_species_list(self):
        self.open("/species")
        names = [self.rows().nth(i).locator("td").first.inner_text() for i in range(self.rows().count())]
        self.assertEqual(names, SAMPLE_NAMES_BY_NAME)
        headers = self.page.locator("thead th").all_inner_texts()
        self.assertEqual(headers, ["Common name", "Scientific name", "Class", "Habitat", "Diet",
                                   "Conservation status"])

    def test_search_species_by_name(self):
        self.open("/species")
        self.page.get_by_label("Search by name", exact=True).fill("lion")
        self.page.get_by_role("button", name="Search").click()
        self.assertEqual(self.rows().count(), 1)
        self.assertEqual(self.rows().first.locator("a").inner_text(), "Lion")
        self.page.get_by_label("Search by name", exact=True).fill("Panthera")
        self.page.get_by_role("button", name="Search").click()
        self.assertEqual(self.rows().count(), 1)
        self.assertIn("Panthera leo", self.rows().first.inner_text())

    def test_filter_species(self):
        self.open("/species")
        self.page.get_by_label("Class", exact=True).select_option("Aves")
        self.page.get_by_role("button", name="Search").click()
        expect(self.page.get_by_text("Showing 3 of 12 species")).to_be_visible()
        self.page.get_by_label("Habitat", exact=True).select_option("Forest")
        self.page.get_by_role("button", name="Search").click()
        expect(self.page.get_by_text("Showing 1 of 12 species")).to_be_visible()
        self.assertEqual(self.rows().first.locator("a").inner_text(), "Japanese bush warbler")
        self.page.get_by_role("link", name="Clear", exact=True).click()
        expect(self.page.get_by_text("Showing 12 of 12 species")).to_be_visible()

    def test_no_match_message(self):
        self.open("/species")
        self.page.get_by_label("Search by name", exact=True).fill("zzzz")
        self.page.get_by_role("button", name="Search").click()
        expect(self.page.get_by_text("No species match your search.")).to_be_visible()
        expect(self.page.get_by_text("Showing 0 of 12 species")).to_be_visible()

    def test_view_species_detail(self):
        self.open("/species")
        self.page.get_by_label("Class", exact=True).select_option("Mammalia")
        self.page.get_by_role("button", name="Search").click()
        self.page.get_by_role("link", name="Lion", exact=True).click()
        expect(self.page.get_by_role("heading", name="Lion", level=1)).to_be_visible()
        details = self.page.locator("dl.details").inner_text()
        for expected in ("Panthera leo", "Felidae", "Grassland", "Carnivore", "VU (Vulnerable)",
                         "14 years", "190 kg"):
            self.assertIn(expected, details)
        self.page.get_by_role("link", name="Back to results").click()
        self.assertIn("class_name=Mammalia", self.page.url)
        expect(self.page.get_by_text("Showing 5 of 12 species")).to_be_visible()

    def test_create_species(self):
        self.open("/species/new")
        self.fill_new_species()
        self.page.get_by_role("button", name="Save").click()
        expect(self.page.get_by_role("heading", name="Arctic fox", level=1)).to_be_visible()
        expect(self.page.get_by_text("Species saved.")).to_be_visible()
        self.open("/species")
        expect(self.page.get_by_text("Showing 13 of 13 species")).to_be_visible()

    def test_validate_species_input(self):
        self.open("/species/new")
        self.page.get_by_label("Average lifespan (years)", exact=True).fill("0")
        self.page.get_by_label("Average adult mass (kg)", exact=True).fill("-1")
        self.page.get_by_role("button", name="Save").click()
        expect(self.page.get_by_text("Please fix the following:")).to_be_visible()
        expect(self.page.locator(".field-error", has_text="Scientific name is required (2 to 100 characters).")).to_be_visible()
        expect(self.page.locator(".field-error", has_text="Average lifespan must be a whole number from 1 to 300.")).to_be_visible()
        expect(self.page.locator(".field-error", has_text="Average adult mass must be a number greater than 0")).to_be_visible()
        self.assertEqual(self.page.get_by_label("Average lifespan (years)", exact=True).input_value(), "0")
        self.assertIn("/species/new", self.page.url)

    def test_unique_scientific_name(self):
        self.open("/species/new")
        self.fill_new_species(**{"Scientific name": "panthera LEO", "Common name": "Lion copy"})
        self.page.get_by_role("button", name="Save").click()
        expect(self.page.locator(".field-error", has_text="This scientific name is already registered.")).to_be_visible()
        self.assertIn("/species/new", self.page.url)

    def test_update_species(self):
        self.open("/species?q=lion")
        self.page.get_by_role("link", name="Lion", exact=True).click()
        self.page.get_by_role("link", name="Edit").click()
        self.page.get_by_label("Description", exact=True).fill("Updated description for lions.")
        self.page.get_by_role("button", name="Save").click()
        expect(self.page.get_by_text("Species saved.")).to_be_visible()
        expect(self.page.get_by_text("Updated description for lions.")).to_be_visible()

    def test_delete_species(self):
        self.open("/species?q=lion")
        self.page.get_by_role("link", name="Lion", exact=True).click()
        self.page.once("dialog", lambda dialog: dialog.dismiss())
        self.page.get_by_role("button", name="Delete", exact=True).click()
        expect(self.page.get_by_role("heading", name="Lion", level=1)).to_be_visible()
        self.page.once("dialog", lambda dialog: dialog.accept())
        self.page.get_by_role("button", name="Delete", exact=True).click()
        expect(self.page.get_by_text("Species deleted.")).to_be_visible()
        expect(self.page.get_by_text("Showing 11 of 11 species")).to_be_visible()

    def test_unknown_species(self):
        self.open("/species/99999")
        expect(self.page.get_by_role("heading", name="Species not found.")).to_be_visible()
        self.page.get_by_role("link", name="Back to species list").click()
        self.assertTrue(self.page.url.endswith("/species"))

    def test_escape_user_input(self):
        self.open("/species/new")
        self.fill_new_species(**{"Scientific name": "Testus escapus", "Common name": "Escape test",
                                 "Description": "<b>bold</b>"})
        self.page.get_by_role("button", name="Save").click()
        expect(self.page.get_by_text("Species saved.")).to_be_visible()
        expect(self.page.get_by_text("<b>bold</b>")).to_be_visible()
        self.assertEqual(self.page.locator("main b").count(), 0)

    def test_color_theme(self):
        self.open("/")
        colors = self.page.evaluate("""() => ({
            body: getComputedStyle(document.body).backgroundColor,
            nav: getComputedStyle(document.querySelector('.site-nav')).backgroundColor,
            button: getComputedStyle(document.querySelector('.button')).backgroundColor,
        })""")
        self.assertEqual(colors["body"], LINEN_RGB)
        self.assertEqual(colors["nav"], MAROON_RGB)
        self.assertEqual(colors["button"], MAROON_RGB)
        self.open("/species")
        colors = self.page.evaluate("""() => ({
            header: getComputedStyle(document.querySelector('thead th')).backgroundColor,
            search: getComputedStyle(document.querySelector('button[type=submit]')).backgroundColor,
            body: getComputedStyle(document.body).backgroundColor,
        })""")
        self.assertEqual(colors["header"], MAROON_RGB)
        self.assertEqual(colors["search"], MAROON_RGB)
        self.assertEqual(colors["body"], LINEN_RGB)

    def test_english_ui(self):
        for path in ("/", "/species", "/species/1", "/species/new", "/species/1/edit", "/species/99999"):
            self.open(path)
            text = self.page.locator("body").inner_text()
            self.assertIsNone(JAPANESE_CHARS.search(text), path)
            self.assertEqual(self.page.evaluate("document.documentElement.lang"), "en")

    def test_response_time(self):
        repository = SpeciesRepository(self.tmp.name)
        for index in range(988):
            repository.create({
                "scientific_name": "Testus speciesis %04d" % index,
                "common_name": "Test species %04d" % index,
                "class_name": "Insecta",
                "family": "",
                "habitat": "Forest",
                "diet": "Herbivore",
                "conservation_status": "LC",
                "average_lifespan_years": None,
                "average_adult_mass_kg": None,
                "description": "",
            })
        checks = [("/species", "Showing 1000 of 1000 species")]
        checks += [("/species?q=test", "Showing 988 of 1000 species")] * 9
        slowest = 0.0
        for path, expected in checks:
            started = time.perf_counter()
            body = urllib.request.urlopen(self.server.url + path, timeout=10).read().decode("utf-8")
            slowest = max(slowest, time.perf_counter() - started)
            self.assertIn(expected, body)
        self.assertLess(slowest, 1.0)

    def test_concurrent_access(self):
        def fetch(_):
            query = urllib.parse.urlencode({"q": "a"})
            return urllib.request.urlopen(self.server.url + "/species?" + query, timeout=10).status

        with ThreadPoolExecutor(max_workers=5) as pool:
            statuses = list(pool.map(fetch, range(5)))
        self.assertEqual(statuses, [200] * 5)


if __name__ == "__main__":
    unittest.main()
