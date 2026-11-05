"""HTTP layer: routes each request to a page or action and sends the HTML response."""

import re
import uuid
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

import views
from poll_service import AlreadyVotedError, NoOptionSelectedError, PollNotFoundError

SURVEY_PATH = re.compile(r"/surveys/(\d+)")
SURVEY_RESULTS_PATH = re.compile(r"/surveys/(\d+)/results")
SURVEY_VOTE_PATH = re.compile(r"/surveys/(\d+)/vote")
MAX_BODY_BYTES = 4096
VOTER_COOKIE = "voter_id"
VOTER_ID_PATTERN = re.compile(r"[0-9a-f]{32}")
VOTER_COOKIE_MAX_AGE = 365 * 24 * 60 * 60


class PollRequestHandler(BaseHTTPRequestHandler):
    """Routes GET and POST requests to the page handlers using the PollService on the server."""

    _voter_id = None
    _issue_voter_cookie = False

    def voter_id(self):
        """Return the browser identifier from the voter cookie, issuing a new one when it is missing or invalid.

        A new identifier is sent back with the next HTML or redirect response as Set-Cookie.
        """
        if self._voter_id is None:
            value = None
            try:
                morsel = SimpleCookie(self.headers.get("Cookie", "")).get(VOTER_COOKIE)
                value = morsel.value if morsel is not None else None
            except CookieError:
                value = None
            if value is not None and VOTER_ID_PATTERN.fullmatch(value):
                self._voter_id = value
            else:
                self._voter_id = uuid.uuid4().hex
                self._issue_voter_cookie = True
        return self._voter_id

    def do_GET(self):
        """Dispatch a GET request to the poll list, vote, result or overview page."""
        parts = urlsplit(self.path)
        path = parts.path
        query = parse_qs(parts.query)
        if path == "/":
            self.handle_poll_list()
            return
        if path == "/results":
            self.handle_all_results()
            return
        match = SURVEY_RESULTS_PATH.fullmatch(path)
        if match:
            self.handle_poll_results(int(match.group(1)), voted=query.get("voted") == ["1"])
            return
        match = SURVEY_PATH.fullmatch(path)
        if match:
            self.handle_vote_page(int(match.group(1)))
            return
        self._send_html(404, views.render_not_found("Page not found."))

    def do_POST(self):
        """Dispatch a POST request to the vote submission action."""
        path = urlsplit(self.path).path
        match = SURVEY_VOTE_PATH.fullmatch(path)
        if match:
            self.handle_vote_submit(int(match.group(1)))
            return
        self._send_html(404, views.render_not_found("Page not found."))

    def handle_poll_list(self):
        """Send the list of all polls."""
        polls = self.server.service.list_polls()
        self._send_html(200, views.render_poll_list(polls))

    def handle_vote_page(self, poll_id, error=None):
        """Send the voting page for one poll, or 404 when the poll does not exist."""
        try:
            detail = self.server.service.get_poll(poll_id)
        except PollNotFoundError:
            self._send_html(404, views.render_not_found("Survey not found."))
            return
        voted = self.server.service.has_voted(poll_id, self.voter_id())
        self._send_html(200, views.render_vote_page(
            detail["poll"], detail["options"], error, already_voted=voted))

    def handle_vote_submit(self, poll_id):
        """Record the selected option, then redirect to the results page.

        When no valid option was chosen, show the voting page again with an error.
        """
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(min(length, MAX_BODY_BYTES)).decode("utf-8", errors="replace")
        raw = parse_qs(body).get("option_id", [None])[0]
        option_id = int(raw) if raw is not None and raw.isdigit() else None
        try:
            self.server.service.cast_vote_once(poll_id, option_id, self.voter_id())
        except PollNotFoundError:
            self._send_html(404, views.render_not_found("Survey not found."))
            return
        except AlreadyVotedError:
            self.handle_vote_page(poll_id)
            return
        except NoOptionSelectedError:
            self.handle_vote_page(poll_id, error="Please select an option.")
            return
        self._send_redirect(f"/surveys/{poll_id}/results?voted=1")

    def handle_poll_results(self, poll_id, voted=False):
        """Send the results of one poll, or 404 when the poll does not exist."""
        try:
            result = self.server.service.get_poll_results(poll_id)
        except PollNotFoundError:
            self._send_html(404, views.render_not_found("Survey not found."))
            return
        self._send_html(200, views.render_poll_results(result, notice=voted))

    def handle_all_results(self):
        """Send the results overview of every poll."""
        results = self.server.service.get_all_results()
        self._send_html(200, views.render_all_results(results))

    def _send_html(self, status, html):
        """Send an HTML response with the given status code."""
        data = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self._send_voter_cookie_if_issued()
        self.end_headers()
        self.wfile.write(data)

    def _send_redirect(self, location):
        """Send a 302 redirect to the given location."""
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self._send_voter_cookie_if_issued()
        self.end_headers()

    def _send_voter_cookie_if_issued(self):
        """Send Set-Cookie for a newly issued browser identifier (HttpOnly, SameSite=Lax, one year)."""
        if self._issue_voter_cookie:
            self.send_header(
                "Set-Cookie",
                f"{VOTER_COOKIE}={self._voter_id}; Path=/; Max-Age={VOTER_COOKIE_MAX_AGE}; "
                "HttpOnly; SameSite=Lax",
            )


def create_server(host, port, service):
    """Return an HTTP server bound to host:port that uses the given PollService."""
    server = HTTPServer((host, port), PollRequestHandler)
    server.service = service
    return server
