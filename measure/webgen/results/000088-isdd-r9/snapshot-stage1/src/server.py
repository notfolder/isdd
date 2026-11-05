"""Web server of the species database (Python standard library only).

Start with run.sh, or directly:  PORT=8000 DATA_DIR=./data python3 src/server.py
"""

import os
import re
import sqlite3
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlsplit

import validation
import views
from repository import SpeciesRepository

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
DEFAULT_PORT = 8000
MAX_BODY_BYTES = 64 * 1024
MAX_ID = 2 ** 63 - 1

SPECIES_PATTERN = re.compile(r"/species/(\d+)")
EDIT_PATTERN = re.compile(r"/species/(\d+)/edit")
DELETE_PATTERN = re.compile(r"/species/(\d+)/delete")

ERROR_TEXT = "Something went wrong. Please try again."
SAVED_NOTICE = "Species saved."
DELETED_NOTICE = "Species deleted."


class SpeciesRequestHandler(BaseHTTPRequestHandler):
    """Routes GET and POST requests to the screens and the form actions."""

    repository = None  # set by main() before the server starts

    def do_GET(self):
        """Show a screen for GET requests."""
        try:
            self._handle_get()
        except Exception:
            self._send_server_error()

    def do_POST(self):
        """Handle the form actions for POST requests."""
        try:
            self._handle_post()
        except Exception:
            self._send_server_error()

    def _handle_get(self):
        parts = urlsplit(self.path)
        path = parts.path.rstrip("/") or "/"
        query = _first_values(parse_qs(parts.query, keep_blank_values=True))
        repo = self.repository

        if path == "/static/style.css":
            self._send_file(os.path.join(STATIC_DIR, "style.css"), "text/css; charset=utf-8")
            return
        if path == "/":
            html = views.render_home(repo.count_species(), repo.count_threatened_species())
            self._send_html(200, html)
            return
        if path == "/species":
            notice = DELETED_NOTICE if query.get("deleted") == "1" else None
            search = validation.parse_search_query(query)
            rows = repo.search(search["text"], search["filters"])
            qs = _query_without(query, ("deleted",))
            self._send_html(200, views.render_species_list(
                rows, search["text"], search["filters"], repo.count_species(), qs, notice=notice))
            return
        if path == "/species/new":
            self._send_html(200, views.render_species_form(
                _blank_values(), {}, "/species/new", "Add species", "/species"))
            return

        match = EDIT_PATTERN.fullmatch(path)
        if match:
            species = self._find_species(match.group(1))
            if species is None:
                return
            values = _values_for_form(species)
            self._send_html(200, views.render_species_form(
                values, {}, "/species/%d/edit" % species["id"], "Edit species",
                "/species/%d" % species["id"]))
            return

        match = SPECIES_PATTERN.fullmatch(path)
        if match:
            species = self._find_species(match.group(1))
            if species is None:
                return
            notice = SAVED_NOTICE if query.get("saved") == "1" else None
            back_query = _query_without(query, ("saved",))
            self._send_html(200, views.render_species_detail(species, back_query, notice=notice))
            return

        self._send_not_found()

    def _handle_post(self):
        path = urlsplit(self.path).path.rstrip("/")
        if path == "/species/new":
            form = self._read_form()
            cleaned, errors = self._check_form(form, exclude_id=None)
            if errors:
                self._send_html(200, views.render_species_form(
                    form, errors, "/species/new", "Add species", "/species"))
                return
            try:
                new_id = self.repository.create(cleaned)
            except sqlite3.IntegrityError:
                errors["scientific_name"] = validation.DUPLICATE_NAME_MESSAGE
                self._send_html(200, views.render_species_form(
                    form, errors, "/species/new", "Add species", "/species"))
                return
            self._redirect("/species/%d?saved=1" % new_id)
            return

        match = EDIT_PATTERN.fullmatch(path)
        if match:
            species = self._find_species(match.group(1))
            if species is None:
                return
            form = self._read_form()
            cleaned, errors = self._check_form(form, exclude_id=species["id"])
            action = "/species/%d/edit" % species["id"]
            cancel = "/species/%d" % species["id"]
            if errors:
                self._send_html(200, views.render_species_form(
                    form, errors, action, "Edit species", cancel))
                return
            try:
                self.repository.update(species["id"], cleaned)
            except sqlite3.IntegrityError:
                errors["scientific_name"] = validation.DUPLICATE_NAME_MESSAGE
                self._send_html(200, views.render_species_form(
                    form, errors, action, "Edit species", cancel))
                return
            self._redirect("/species/%d?saved=1" % species["id"])
            return

        match = DELETE_PATTERN.fullmatch(path)
        if match:
            species = self._find_species(match.group(1))
            if species is None:
                return
            self.repository.delete(species["id"])
            self._redirect("/species?deleted=1")
            return

        self._send_not_found()

    def _check_form(self, form, exclude_id):
        cleaned, errors = validation.validate_species_fields(form)
        if "scientific_name" not in errors and self.repository.is_scientific_name_taken(
                cleaned["scientific_name"], exclude_id=exclude_id):
            errors["scientific_name"] = validation.DUPLICATE_NAME_MESSAGE
        return cleaned, errors

    def _find_species(self, id_text):
        """Return the species for an id in the path, or send the not-found screen and return None."""
        species_id = int(id_text)
        species = self.repository.get(species_id) if 0 < species_id <= MAX_ID else None
        if species is None:
            self._send_not_found()
        return species

    def _read_form(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY_BYTES:
            length = MAX_BODY_BYTES
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        return _first_values(parse_qs(body, keep_blank_values=True))

    def _redirect(self, location):
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send_html(self, status, html):
        data = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, path, content_type):
        with open(path, "rb") as handle:
            data = handle.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_not_found(self):
        self._send_html(404, views.render_not_found())

    def _send_server_error(self):
        traceback.print_exc()
        try:
            html = views.render_layout("Error", "<h1>%s</h1>\n" % ERROR_TEXT)
            self._send_html(500, html)
        except Exception:
            self.send_error(500)


def _first_values(parsed):
    return {key: values[0] for key, values in parsed.items()}


def _query_without(query, names):
    kept = [(key, value) for key, value in query.items() if key not in names and value != ""]
    return urlencode(kept)


def _blank_values():
    return {name: "" for name in (
        "scientific_name", "common_name", "class_name", "family", "habitat", "diet",
        "conservation_status", "average_lifespan_years", "average_adult_mass_kg", "description")}


def _values_for_form(species):
    values = _blank_values()
    for name in values:
        value = species.get(name)
        values[name] = "" if value is None else str(value)
    return values


def main():
    """Read PORT and DATA_DIR, prepare the database and serve until interrupted."""
    try:
        port = int(os.environ.get("PORT", DEFAULT_PORT))
    except ValueError:
        print("PORT must be a number", file=sys.stderr)
        return 1
    data_dir = os.environ.get("DATA_DIR") or os.path.join(PROJECT_ROOT, "data")

    repository = SpeciesRepository(data_dir)
    repository.initialize()
    SpeciesRequestHandler.repository = repository

    server = ThreadingHTTPServer(("0.0.0.0", port), SpeciesRequestHandler)
    print("Species Database is running at http://127.0.0.1:%d (DATA_DIR=%s)" % (port, data_dir), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
