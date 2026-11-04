"""E2E テスト（詳細設計書 8-2）。実サーバーを 127.0.0.1 で起動し、HTTP で各場面を確かめる。

各テストは一時ディレクトリを DATA_DIR にした新しいサーバーを起動し、終わったら自分で起動したプロセスだけを止める。
"""

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """302 を自動で追わず、転送先を確かめられるようにする。"""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@contextmanager
def running_server(data_dir: Optional[str] = None) -> Iterator[str]:
    """DATA_DIR を指定しなければ空の一時ディレクトリで実サーバーを起動し、ベース URL を返す。終了時に自分のプロセスだけを止める。"""
    own_dir = data_dir is None
    if own_dir:
        data_dir = tempfile.mkdtemp(prefix="species-e2e-")
    port = _free_port()
    python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    env = dict(os.environ, PORT=str(port), DATA_DIR=data_dir)
    process = subprocess.Popen(
        [python, "-m", "app"], cwd=str(ROOT), env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 30
        while True:
            try:
                status, _, _ = request(base, "GET", "/")
                if status == 200:
                    break
            except (urllib.error.URLError, ConnectionError, OSError):
                pass
            if process.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError("the species server did not start")
            time.sleep(0.2)
        yield base
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
        if own_dir:
            shutil.rmtree(data_dir, ignore_errors=True)


def request(base: str, method: str, path: str, form: Optional[dict] = None) -> tuple[int, dict, str]:
    """HTTP を 1 回呼ぶ。戻り値は (状態コード, ヘッダー, 本文)。302 は追わない。"""
    data = urllib.parse.urlencode(form).encode("utf-8") if form is not None else None
    http_request = urllib.request.Request(base + path, data=data, method=method)
    try:
        response = _OPENER.open(http_request, timeout=10)
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), error.read().decode("utf-8")
    return response.status, dict(response.headers), response.read().decode("utf-8")


# 旧い定義（学名、界、保全状況が NOT NULL）の species 表。移行の E2E で使う。
_LEGACY_SCHEMA = """
CREATE TABLE species (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scientific_name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    common_name TEXT NOT NULL,
    kingdom TEXT NOT NULL,
    taxonomic_class TEXT,
    habitat TEXT NOT NULL,
    diet TEXT NOT NULL,
    conservation_status TEXT NOT NULL,
    average_length_cm REAL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
INSERT INTO species (scientific_name, common_name, kingdom, taxonomic_class, habitat, diet,
    conservation_status, average_length_cm, description, created_at, updated_at)
VALUES ('Vulpes vulpes', 'Red fox', 'Animalia', 'Mammalia', 'Terrestrial', 'Omnivore', 'LC', 70.5,
    'Adaptable fox.', '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00');
"""


def _new_species_form(**overrides: str) -> dict:
    form = {
        "scientific_name": "Vulpes vulpes",
        "common_name": "Red fox",
        "kingdom": "Animalia",
        "taxonomic_class": "Mammalia",
        "habitat": "Terrestrial",
        "diet": "Omnivore",
        "conservation_status": "LC",
        "average_length_cm": "70.5",
        "description": "Adaptable fox found across the Northern Hemisphere.",
    }
    form.update(overrides)
    return form


class SpeciesSiteE2ETest(unittest.TestCase):
    def test_startup_with_sample_data(self) -> None:
        with running_server() as base:
            status, _, body = request(base, "GET", "/")
            self.assertEqual(status, 200)
            self.assertIn('<p class="count">12 species</p>', body)
            self.assertIn("Lion", body)

    def test_browse_and_view_species(self) -> None:
        with running_server() as base:
            status, _, body = request(base, "GET", "/")
            self.assertEqual(status, 200)
            self.assertIn('href="/species/1"', body)
            status, _, detail = request(base, "GET", "/species/1")
            self.assertEqual(status, 200)
            for label in ("Scientific name", "Common name", "Kingdom", "Class", "Habitat", "Diet",
                          "Conservation status", "Average length", "Description"):
                self.assertIn(label, detail)
            for nav_text in ("Browse species", "Add species", "Species Database"):
                self.assertIn(nav_text, detail)

    def test_search_species_keyword(self) -> None:
        with running_server() as base:
            status, _, body = request(base, "GET", "/?q=lion")
            self.assertEqual(status, 200)
            self.assertIn('<p class="count">1 species</p>', body)
            self.assertIn("Panthera leo", body)
            _, _, empty = request(base, "GET", "/?q=zzzz")
            self.assertIn("No species match", empty)

    def test_filter_and_combine(self) -> None:
        with running_server() as base:
            _, _, marine = request(base, "GET", "/?kingdom=Animalia&habitat=Marine")
            self.assertIn('<p class="count">1 species</p>', marine)
            self.assertIn("Mesoplodon perrini", marine)
            _, _, combined = request(base, "GET", "/?kingdom=Animalia&q=lion")
            self.assertIn('<p class="count">1 species</p>', combined)
            _, _, cleared = request(base, "GET", "/")
            self.assertIn('<p class="count">12 species</p>', cleared)

    def test_add_species_form(self) -> None:
        with running_server() as base:
            status, _, page = request(base, "GET", "/species/new")
            self.assertEqual(status, 200)
            for field in ('name="common_name"', 'name="habitat"', 'name="diet"', 'name="description"'):
                self.assertIn(field, page)
            form = {"common_name": "Test Gecko", "habitat": "Terrestrial", "diet": "Carnivore",
                    "description": "A test entry."}
            status, headers, _ = request(base, "POST", "/species/new", form)
            self.assertEqual(status, 302)
            self.assertIn("/species/13?saved=1", headers.get("Location", ""))
            _, _, listing = request(base, "GET", "/")
            self.assertIn('<p class="count">13 species</p>', listing)
            self.assertIn("Test Gecko", listing)
            _, _, by_keyword = request(base, "GET", "/?q=gecko")
            self.assertIn('<p class="count">1 species</p>', by_keyword)
            _, _, by_filter = request(base, "GET", "/?habitat=Terrestrial&diet=Carnivore")
            self.assertIn("Test Gecko", by_filter)
            status, _, duplicate = request(
                base, "POST", "/species/new",
                {"scientific_name": "panthera LEO", "common_name": "Fake lion", "habitat": "Terrestrial",
                 "diet": "Carnivore", "description": ""},
            )
            self.assertEqual(status, 200)
            self.assertIn("This scientific name is already registered.", duplicate)
            self.assertIn('value="Fake lion"', duplicate)
            _, _, after = request(base, "GET", "/")
            self.assertIn('<p class="count">13 species</p>', after)

    def test_migrate_existing_database(self) -> None:
        data_dir = tempfile.mkdtemp(prefix="species-legacy-")
        try:
            import sqlite3
            connection = sqlite3.connect(os.path.join(data_dir, "species.db"))
            connection.executescript(_LEGACY_SCHEMA)
            connection.commit()
            connection.close()
            with running_server(data_dir) as base:
                _, _, listing = request(base, "GET", "/")
                self.assertIn('<p class="count">1 species</p>', listing)
                self.assertIn("Red fox", listing)
                status, headers, _ = request(
                    base, "POST", "/species/new",
                    {"common_name": "No name gecko", "habitat": "Marine", "diet": "Other", "description": ""},
                )
                self.assertEqual(status, 302)
                self.assertIn("/species/2?saved=1", headers.get("Location", ""))
        finally:
            shutil.rmtree(data_dir, ignore_errors=True)

    def test_update_species_record(self) -> None:
        with running_server() as base:
            status, _, _ = request(base, "GET", "/species/1/edit")
            self.assertEqual(status, 200)
            status, headers, _ = request(
                base, "POST", "/species/1/edit",
                _new_species_form(scientific_name="Panthera leo", common_name="African lion", habitat="Terrestrial"),
            )
            self.assertEqual(status, 302)
            self.assertIn("/species/1?saved=1", headers.get("Location", ""))
            _, _, detail = request(base, "GET", "/species/1")
            self.assertIn("African lion", detail)

    def test_delete_species_record(self) -> None:
        with running_server() as base:
            status, _, confirm = request(base, "GET", "/species/1/delete")
            self.assertEqual(status, 200)
            self.assertIn("Delete species?", confirm)
            status, _, _ = request(base, "GET", "/species/1")
            self.assertEqual(status, 200)
            status, headers, _ = request(base, "POST", "/species/1/delete")
            self.assertEqual(status, 302)
            self.assertIn("notice=deleted", headers.get("Location", ""))
            _, _, listing = request(base, "GET", "/?notice=deleted")
            self.assertIn("Species deleted.", listing)
            self.assertIn('<p class="count">11 species</p>', listing)
            status, _, _ = request(base, "GET", "/species/1")
            self.assertEqual(status, 404)

    def test_theme_honeydew_olive(self) -> None:
        with running_server() as base:
            for path in ("/", "/species/1", "/species/new"):
                status, _, body = request(base, "GET", path)
                self.assertEqual(status, 200, path)
                self.assertIn("/static/style.css", body)
            status, _, css = request(base, "GET", "/static/style.css")
            self.assertEqual(status, 200)
            self.assertIn("--base-honeydew: #F0FFF0;", css)
            self.assertIn("--olive: #556B2F;", css)
            self.assertIn("background: var(--base-honeydew);", css)
            self.assertNotIn("#FAF0E6", css)
            self.assertNotIn("#800000", css)


if __name__ == "__main__":
    unittest.main()
