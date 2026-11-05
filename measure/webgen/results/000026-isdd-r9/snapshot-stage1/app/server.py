"""HTTP entry point: routes requests to PollService and renders HTML with views."""

from __future__ import annotations

import re
import secrets
import sys
import traceback
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs

import views
from config import load_data_dir, load_port
from db import Database
from polls import (
    VOTE_ALREADY_VOTED,
    VOTE_INVALID_OPTION,
    VOTE_NO_OPTION,
    VOTE_NOT_FOUND,
    VOTE_OK,
    PollService,
)
from seed import SampleSeeder

HOST = "127.0.0.1"
COOKIE_NAME = "voter"
TOKEN_PATTERN = re.compile(r"^[0-9a-f]{32}$")
POLL_PATH = re.compile(r"^/polls/(\d+)$")
POLL_VOTE_PATH = re.compile(r"^/polls/(\d+)/vote$")
POLL_RESULTS_PATH = re.compile(r"^/polls/(\d+)/results$")


class PollsHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], service: PollService) -> None:
        super().__init__(address, PollsRequestHandler)
        self.service = service


class PollsRequestHandler(BaseHTTPRequestHandler):
    server_version = "PollsSite/1.0"

    @property
    def service(self) -> PollService:
        return self.server.service  # type: ignore[attr-defined]

    def do_GET(self) -> None:
        self._guard(self._route_get)

    def do_POST(self) -> None:
        self._guard(self._route_post)

    def _guard(self, route: Any) -> None:
        """Run a route; on an unexpected error (for example a database failure) show the 500 page."""
        try:
            route()
        except Exception:
            traceback.print_exc()
            self._html(HTTPStatus.INTERNAL_SERVER_ERROR, views.message_page("Error", "Something went wrong."))

    def _route_get(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/":
            self._redirect("/polls")
        elif path == "/polls":
            self._html(HTTPStatus.OK, views.poll_list_page(self.service.list_polls()))
        elif m := POLL_PATH.match(path):
            self._show_poll(int(m.group(1)))
        elif m := POLL_RESULTS_PATH.match(path):
            self._show_results(int(m.group(1)))
        elif path == "/results":
            self._html(HTTPStatus.OK, views.results_list_page(self.service.list_results()))
        else:
            self._not_found()

    def _route_post(self) -> None:
        path = self.path.split("?", 1)[0]
        if m := POLL_VOTE_PATH.match(path):
            self._cast_vote(int(m.group(1)))
        else:
            self._not_found()

    # --- screens -----------------------------------------------------------

    def _show_poll(self, poll_id: int) -> None:
        poll = self.service.get_poll(poll_id)
        if poll is None:
            self._not_found()
            return
        self._html(HTTPStatus.OK, views.poll_vote_page(poll))

    def _show_results(self, poll_id: int) -> None:
        data = self.service.get_results(poll_id)
        if data is None:
            self._not_found()
            return
        self._html(HTTPStatus.OK, views.poll_results_page(data))

    def _cast_vote(self, poll_id: int) -> None:
        length = int(self.headers.get("Content-Length", "0") or 0)
        form = parse_qs(self.rfile.read(length).decode("utf-8", errors="replace"))
        raw_option = form.get("option", [""])[0].strip()
        option_id: int | None
        if raw_option == "":
            option_id = None
        elif raw_option.isdigit():
            option_id = int(raw_option)
        else:
            option_id = -1  # never matches an option, so it is reported as invalid

        voter, is_new = self._voter_token()
        result = self.service.cast_vote(poll_id, option_id, voter)
        extra = {"Set-Cookie": self._cookie_header(voter)} if is_new else {}

        if result == VOTE_OK:
            self._redirect(f"/polls/{poll_id}/results", extra)
            return
        if result == VOTE_NOT_FOUND:
            self._not_found(extra)
            return
        poll = self.service.get_poll(poll_id)
        if poll is None:  # removed between the two reads; treat as not found
            self._not_found(extra)
            return
        if result in (VOTE_NO_OPTION, VOTE_INVALID_OPTION):
            page = views.poll_vote_page(poll, error="Please select an option.")
            self._html(HTTPStatus.BAD_REQUEST, page, extra)
        elif result == VOTE_ALREADY_VOTED:
            page = views.poll_vote_page(poll, notice="You have already voted in this poll.")
            self._html(HTTPStatus.OK, page, extra)

    def _not_found(self, extra: dict[str, str] | None = None) -> None:
        page = views.message_page("Not found", "Poll not found.")
        self._html(HTTPStatus.NOT_FOUND, page, extra)

    # --- helpers -----------------------------------------------------------

    def _voter_token(self) -> tuple[str, bool]:
        """Return the voter token from the cookie, or a new one and True when none is valid."""
        cookie = SimpleCookie()
        cookie.load(self.headers.get("Cookie", ""))
        morsel = cookie.get(COOKIE_NAME)
        if morsel and TOKEN_PATTERN.match(morsel.value):
            return morsel.value, False
        return secrets.token_hex(16), True

    @staticmethod
    def _cookie_header(token: str) -> str:
        return f"{COOKIE_NAME}={token}; Path=/; HttpOnly; SameSite=Lax"

    def _html(self, status: HTTPStatus, body: str, extra: dict[str, str] | None = None) -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        for name, value in (extra or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(payload)

    def _redirect(self, location: str, extra: dict[str, str] | None = None) -> None:
        status = HTTPStatus.SEE_OTHER if self.command == "POST" else HTTPStatus.FOUND
        self.send_response(status)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        for name, value in (extra or {}).items():
            self.send_header(name, value)
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - matches the base signature
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))


def build_server(port: int, data_dir_path: str | None = None) -> PollsHTTPServer:
    """Create the database, seed sample data when empty, and bind the HTTP server."""
    data_dir = load_data_dir() if data_dir_path is None else _ensure_dir(data_dir_path)
    db = Database(data_dir / "polls.db")
    db.ensure_schema()
    SampleSeeder(db).seed_if_empty()
    return PollsHTTPServer((HOST, port), PollService(db))


def _ensure_dir(path: str):
    from pathlib import Path

    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def main() -> None:
    port = load_port()
    server = build_server(port)
    print(f"Polls website running at http://{HOST}:{port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
