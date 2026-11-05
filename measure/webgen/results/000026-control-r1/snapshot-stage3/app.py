#!/usr/bin/env python3
"""Surveys website: voting and viewing results.

Standard library only (http.server + sqlite3), so no dependencies are needed.
Configuration comes from environment variables:
  PORT      - port to listen on (default 8000), bound to 127.0.0.1
  DATA_DIR  - directory for the SQLite database (default ./data)
"""
import html
import os
import re
import secrets
import sqlite3
import sys
import time
import traceback
from contextlib import closing
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(BASE_DIR, "data")
PORT = int(os.environ.get("PORT") or "8000")
DB_PATH = os.path.join(DATA_DIR, "polls.db")

MAX_OPTIONS = 20
MAX_OPTION_LEN = 200
MAX_QUESTION_LEN = 300
MAX_DESCRIPTION_LEN = 1000
MAX_BODY = 200_000

SCHEMA = """
CREATE TABLE IF NOT EXISTS polls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL REFERENCES polls(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    position INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL REFERENCES polls(id) ON DELETE CASCADE,
    option_id INTEGER NOT NULL REFERENCES options(id) ON DELETE CASCADE,
    voter TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    UNIQUE (poll_id, voter)
);
"""

# Sample content shown when the database is empty so every feature can be tried.
SAMPLE_POLLS = [
    (
        "What is your favorite programming language?",
        "Pick the language you enjoy using the most.",
        [("Python", 9), ("JavaScript", 7), ("Go", 4), ("Rust", 5), ("Other", 1)],
    ),
    (
        "Where should our next team offsite be?",
        "The whole team will vote on one city.",
        [("Kyoto", 6), ("Lisbon", 8), ("Toronto", 3), ("Cape Town", 2)],
    ),
    (
        "Which feature should we build next?",
        "Your votes help us prioritize the roadmap.",
        [("Dark mode", 5), ("Offline support", 3), ("Calendar sync", 6), ("Mobile app", 4)],
    ),
]

NAV = [
    ("surveys", "/", "Surveys"),
    ("results", "/results", "Results"),
    ("create", "/create", "Create Survey"),
]


# ---------------------------------------------------------------- database

def connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def seed(conn):
    now = int(time.time())
    for n, (question, description, options) in enumerate(SAMPLE_POLLS):
        cur = conn.execute(
            "INSERT INTO polls (question, description, created_at) VALUES (?, ?, ?)",
            (question, description, now - (len(SAMPLE_POLLS) - n) * 3600),
        )
        poll_id = cur.lastrowid
        for position, (text, count) in enumerate(options):
            opt = conn.execute(
                "INSERT INTO options (poll_id, text, position) VALUES (?, ?, ?)",
                (poll_id, text, position),
            )
            for k in range(count):
                conn.execute(
                    "INSERT INTO votes (poll_id, option_id, voter, created_at) VALUES (?, ?, ?, ?)",
                    (poll_id, opt.lastrowid, "sample-%d-%d-%d" % (poll_id, position, k), now),
                )
    conn.commit()


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    with closing(connect()) as conn:
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM polls").fetchone()[0] == 0:
            seed(conn)


def get_poll(conn, poll_id):
    return conn.execute("SELECT * FROM polls WHERE id = ?", (poll_id,)).fetchone()


def get_results(conn, poll_id):
    rows = conn.execute(
        """
        SELECT o.id, o.text, COUNT(v.id) AS votes
        FROM options o
        LEFT JOIN votes v ON v.option_id = o.id
        WHERE o.poll_id = ?
        GROUP BY o.id
        ORDER BY o.position, o.id
        """,
        (poll_id,),
    ).fetchall()
    total = sum(r["votes"] for r in rows)
    results = []
    for r in rows:
        percent = r["votes"] * 100.0 / total if total else 0.0
        results.append({"id": r["id"], "text": r["text"], "votes": r["votes"], "percent": percent})
    return results, total


def list_polls(conn, voter):
    return conn.execute(
        """
        SELECT p.id, p.question, p.description, p.created_at,
               (SELECT COUNT(*) FROM votes v WHERE v.poll_id = p.id) AS total_votes,
               (SELECT COUNT(*) FROM options o WHERE o.poll_id = p.id) AS option_count,
               (SELECT COUNT(*) FROM votes v WHERE v.poll_id = p.id AND v.voter = ?) AS mine
        FROM polls p
        ORDER BY p.created_at DESC, p.id DESC
        """,
        (voter,),
    ).fetchall()


def has_voted(conn, poll_id, voter):
    return conn.execute(
        "SELECT 1 FROM votes WHERE poll_id = ? AND voter = ?", (poll_id, voter)
    ).fetchone() is not None


# ---------------------------------------------------------------- rendering helpers

def esc(value):
    return html.escape(str(value), quote=True)


def layout(title, body, active=""):
    links = []
    for key, href, label in NAV:
        cls = ' class="active"' if key == active else ""
        links.append('<a href="%s"%s>%s</a>' % (href, cls, label))
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>" + esc(title) + " · Surveys</title>\n"
        "<style>" + CSS + "</style>\n"
        "</head>\n<body>\n"
        '<header class="site"><div class="inner">'
        '<a class="brand" href="/">Surveys</a>'
        '<nav aria-label="Main navigation">' + "".join(links) + "</nav>"
        "</div></header>\n"
        "<main>\n" + body + "\n</main>\n"
        '<footer class="site-footer">Cast your vote, then check the results.</footer>\n'
        "</body>\n</html>\n"
    )


def notice(message, kind=""):
    cls = "notice" + (" " + kind if kind else "")
    return '<div class="%s" role="status">%s</div>' % (cls, esc(message))


def poll_card(p):
    description = '<p>%s</p>' % esc(p["description"]) if p["description"] else ""
    badge = '<span class="badge">You have already voted</span>' if p["mine"] else ""
    return (
        '<article class="card">'
        '<h2><a href="/surveys/%d">%s</a>%s</h2>' % (p["id"], esc(p["question"]), badge)
        + description
        + '<p class="meta">%d options · %d vote%s</p>'
        % (p["option_count"], p["total_votes"], "" if p["total_votes"] == 1 else "s")
        + '<div class="actions">'
        '<a class="button" href="/surveys/%d">Vote</a> '
        '<a class="button secondary" href="/results/%d">View results</a>'
        "</div></article>" % (p["id"], p["id"])
    )


def results_block(results, total):
    if total == 0:
        heading = '<p class="empty">No votes have been cast yet.</p>'
    else:
        heading = '<p class="total">Total votes: %d</p>' % total
    rows = []
    for o in results:
        rows.append(
            '<div class="result-row">'
            '<div class="result-label"><span>%s</span>'
            "<span>%d vote%s (%.1f%%)</span></div>"
            '<div class="bar"><div class="fill" style="width:%.1f%%"></div></div>'
            "</div>"
            % (esc(o["text"]), o["votes"], "" if o["votes"] == 1 else "s", o["percent"], o["percent"])
        )
    return heading + "".join(rows)


def vote_form(poll_id, results, disabled=False):
    dis_attr = " disabled" if disabled else ""
    radios = "".join(
        '<label class="option%s"><input type="radio" name="option" value="%d" required%s>'
        "<span>%s</span></label>" % (" disabled" if disabled else "", o["id"], dis_attr, esc(o["text"]))
        for o in results
    )
    return (
        '<form method="post" action="/surveys/%d/vote" class="vote-form">' % poll_id
        + '<fieldset><legend>Choose one option</legend>' + radios + "</fieldset>"
        + '<button type="submit"%s>Cast my vote</button>' % dis_attr
        + "</form>"
    )


CSS = """
*{box-sizing:border-box}
body{margin:0;background:#ffffe0;color:#2f4f4f;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;line-height:1.5;min-height:100vh;display:flex;flex-direction:column}
a{color:#2f4f4f}
header.site{background:#2f4f4f;color:#ffffe0}
header.site .inner{max-width:900px;margin:0 auto;padding:14px 20px;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px}
header.site .brand{color:#ffffe0;font-size:1.4rem;font-weight:700;text-decoration:none}
header.site nav a{color:#ffffe0;text-decoration:none;margin-left:12px;padding:6px 12px;border-radius:6px;display:inline-block}
header.site nav a:hover{background:rgba(255,255,224,.18)}
header.site nav a.active{background:#ffffe0;color:#2f4f4f;font-weight:600}
main{flex:1;width:100%;max-width:900px;margin:0 auto;padding:28px 20px 48px}
h1{color:#2f4f4f;margin:0 0 8px;font-size:2rem}
h2{color:#2f4f4f;font-size:1.25rem;margin:0 0 6px}
h2 a{color:#2f4f4f;text-decoration:none}
h2 a:hover{text-decoration:underline}
p.lead{color:#4f6b6b;margin-top:0}
.card{background:#fafad2;border:2px solid #2f4f4f;border-radius:10px;padding:18px 20px;margin-bottom:16px}
.meta{color:#4f6b6b;font-size:.92rem;margin:4px 0 12px}
.actions{display:flex;flex-wrap:wrap;gap:10px}
.button,button{display:inline-block;background:#2f4f4f;color:#ffffe0;border:2px solid #2f4f4f;border-radius:6px;padding:9px 18px;font:inherit;font-weight:600;text-decoration:none;cursor:pointer}
.button:hover,button:hover{background:#44696a;border-color:#44696a;color:#ffffe0}
button:disabled{background:#8fa3a3;border-color:#8fa3a3;color:#ffffe0;cursor:not-allowed}
.button.secondary{background:#ffffe0;color:#2f4f4f}
.button.secondary:hover{background:#fafad2;color:#2f4f4f}
.actions-row{margin:18px 0}
.notice{border-left:6px solid #2f4f4f;background:#fafad2;color:#2f4f4f;padding:12px 16px;border-radius:6px;margin-bottom:20px;font-weight:600}
.notice.error{border-left-color:#8a0018;background:#f6d5d5;color:#8a0018}
form.vote-form fieldset{border:2px solid #2f4f4f;border-radius:10px;padding:14px 20px 18px;margin:0 0 18px;background:#fafad2}
legend{color:#2f4f4f;font-weight:700;padding:0 6px}
label.option{display:flex;align-items:center;gap:10px;padding:10px 12px;border:1px solid #8fa3a3;border-radius:6px;margin:8px 0;cursor:pointer}
label.option:hover{border-color:#2f4f4f;background:#f5f5c4}
label.option.disabled{cursor:not-allowed;opacity:.6}
label.option.disabled:hover{border-color:#8fa3a3;background:transparent}
input[type=radio]{accent-color:#2f4f4f;width:18px;height:18px;margin:0}
input[type=radio]:disabled{accent-color:#8fa3a3}
form.create-form label{display:block;font-weight:600;color:#2f4f4f;margin-bottom:16px}
form.create-form .hint{display:block;font-weight:400;color:#4f6b6b;font-size:.9rem}
input[type=text],textarea{display:block;width:100%;padding:9px 10px;border:2px solid #2f4f4f;border-radius:6px;font:inherit;color:#2f4f4f;margin-top:6px;background:#ffffe0}
input[type=text]:focus,textarea:focus{outline:3px solid #8fa3a3;outline-offset:1px}
.bar{background:#f0eec0;border-radius:999px;height:16px;overflow:hidden}
.fill{background:#2f4f4f;height:100%;border-radius:999px}
.result-row{margin:16px 0}
.result-label{display:flex;justify-content:space-between;gap:12px;margin-bottom:4px;font-weight:600}
.total{font-size:1.1rem;color:#2f4f4f;font-weight:700}
.empty{color:#4f6b6b}
.error-text{color:#8a0018;font-weight:600}
.badge{display:inline-block;background:#2f4f4f;color:#ffffe0;border-radius:999px;padding:2px 10px;font-size:.85rem;font-weight:600;margin-left:8px;vertical-align:middle}
.site-footer{background:#2f4f4f;color:#ffffe0;text-align:center;padding:14px 20px;font-size:.92rem}
"""


# ---------------------------------------------------------------- HTTP handler

class Handler(BaseHTTPRequestHandler):
    server_version = "Surveys/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def do_GET(self):
        self.handle_request("GET")

    def do_POST(self):
        self.handle_request("POST")

    # -- request plumbing

    def handle_request(self, method):
        self.new_voter = None
        self.voter = self.cookie_voter()
        if self.voter is None:
            self.voter = secrets.token_hex(16)
            self.new_voter = self.voter
        try:
            parts = urlsplit(self.path)
            path = parts.path if parts.path == "/" else parts.path.rstrip("/")
            query = parse_qs(parts.query)
            self.dispatch(method, path, query)
        except Exception:
            traceback.print_exc()
            self.send_page(500, layout("Error", self.error_body(
                "Something went wrong", "The server could not process your request. Please try again.")))

    def dispatch(self, method, path, query):
        m = re.fullmatch(r"/surveys/(\d+)", path)
        if method == "GET":
            if path == "/":
                return self.page_home()
            if m:
                return self.page_poll(int(m.group(1)), query)
            if path == "/results":
                return self.page_results_list()
            m = re.fullmatch(r"/results/(\d+)", path)
            if m:
                return self.page_results(int(m.group(1)), query)
            if path == "/create":
                return self.page_create_form()
        elif method == "POST":
            m = re.fullmatch(r"/surveys/(\d+)/vote", path)
            if m:
                return self.post_vote(int(m.group(1)))
            if path == "/create":
                return self.post_create()
        return self.not_found()

    def cookie_voter(self):
        jar = cookies.SimpleCookie()
        try:
            jar.load(self.headers.get("Cookie", ""))
        except cookies.CookieError:
            return None
        morsel = jar.get("voter")
        if morsel and re.fullmatch(r"[0-9a-f]{32}", morsel.value):
            return morsel.value
        return None

    def read_form(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        raw = self.rfile.read(min(length, MAX_BODY)).decode("utf-8", "replace")
        return parse_qs(raw, keep_blank_values=True)

    def _common_headers(self):
        if self.new_voter:
            self.send_header(
                "Set-Cookie",
                "voter=%s; Path=/; Max-Age=31536000; HttpOnly; SameSite=Lax" % self.new_voter,
            )

    def send_page(self, status, body):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self._common_headers()
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def redirect(self, location):
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self._common_headers()
        self.end_headers()

    @staticmethod
    def field(form, name):
        return form.get(name, [""])[0]

    def error_body(self, title, message):
        return (
            '<h1>%s</h1>' % esc(title)
            + '<p class="error-text">%s</p>' % esc(message)
            + '<p class="actions-row"><a class="button" href="/">Back to all surveys</a></p>'
        )

    def not_found(self):
        self.send_page(404, layout("Not found", self.error_body(
            "Page not found", "The page you are looking for does not exist.")))

    # -- pages

    def page_home(self):
        with closing(connect()) as conn:
            polls = list_polls(conn, self.voter)
        if polls:
            items = "".join(poll_card(p) for p in polls)
        else:
            items = '<p class="empty">No surveys yet. <a href="/create">Create the first one</a>.</p>'
        body = (
            "<h1>Open surveys</h1>"
            '<p class="lead">Browse the surveys below, cast your vote, or see what others chose.</p>'
            + items
        )
        self.send_page(200, layout("Surveys", body, active="surveys"))

    def page_poll(self, poll_id, query):
        with closing(connect()) as conn:
            poll = get_poll(conn, poll_id)
            if poll is None:
                return self.not_found()
            results, total = get_results(conn, poll_id)
            voted = has_voted(conn, poll_id, self.voter)

        parts = []
        if query.get("created"):
            parts.append(notice("Your survey has been created. Share it and start collecting votes!"))
        if voted:
            parts.append(notice("You have already voted in this survey. Current results are shown below."))
        parts.append("<h1>%s</h1>" % esc(poll["question"]))
        if poll["description"]:
            parts.append('<p class="lead">%s</p>' % esc(poll["description"]))
        # One vote per survey per browser: the controls stay visible but disabled once voted.
        parts.append(vote_form(poll_id, results, disabled=voted))
        if voted:
            parts.append(results_block(results, total))
        parts.append('<p class="actions-row"><a class="button secondary" href="/results/%d">View results</a></p>' % poll_id)
        self.send_page(200, layout(poll["question"], "".join(parts), active="surveys"))

    def post_vote(self, poll_id):
        form = self.read_form()
        option_raw = self.field(form, "option").strip()
        with closing(connect()) as conn:
            poll = get_poll(conn, poll_id)
            if poll is None:
                return self.not_found()
            option = None
            if option_raw.isdigit():
                option = conn.execute(
                    "SELECT id FROM options WHERE id = ? AND poll_id = ?",
                    (int(option_raw), poll_id),
                ).fetchone()
            if option is None:
                body = self.error_body("No option selected", "Please choose one option before casting your vote.")
                body = body.replace(
                    '<a class="button" href="/">Back to all surveys</a>',
                    '<a class="button" href="/surveys/%d">Back to the survey</a>' % poll_id,
                )
                return self.send_page(400, layout("Vote not recorded", body, active="surveys"))

            if has_voted(conn, poll_id, self.voter):
                return self.redirect("/surveys/%d" % poll_id)
            try:
                conn.execute(
                    "INSERT INTO votes (poll_id, option_id, voter, created_at) VALUES (?, ?, ?, ?)",
                    (poll_id, option["id"], self.voter, int(time.time())),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                # Another request from the same voter won the race; the vote is already recorded.
                conn.rollback()
                return self.redirect("/surveys/%d" % poll_id)
        self.redirect("/results/%d?voted=1" % poll_id)

    def page_results_list(self):
        with closing(connect()) as conn:
            polls = list_polls(conn, self.voter)
        if polls:
            rows = []
            for p in polls:
                rows.append(
                    '<article class="card">'
                    '<h2><a href="/results/%d">%s</a></h2>' % (p["id"], esc(p["question"]))
                    + '<p class="meta">%d option%s · %d vote%s so far</p>'
                    % (p["option_count"], "" if p["option_count"] == 1 else "s",
                       p["total_votes"], "" if p["total_votes"] == 1 else "s")
                    + '<div class="actions"><a class="button secondary" href="/results/%d">View results</a></div>'
                    % p["id"]
                    + "</article>"
                )
            items = "".join(rows)
        else:
            items = '<p class="empty">No surveys yet, so there are no results to show.</p>'
        body = "<h1>Results</h1><p class=\"lead\">See how the votes stand in every survey.</p>" + items
        self.send_page(200, layout("Results", body, active="results"))

    def page_results(self, poll_id, query):
        with closing(connect()) as conn:
            poll = get_poll(conn, poll_id)
            if poll is None:
                return self.not_found()
            results, total = get_results(conn, poll_id)
            voted = has_voted(conn, poll_id, self.voter)
        parts = []
        if query.get("voted"):
            parts.append(notice("Thanks! Your vote has been recorded."))
        parts.append("<h1>%s</h1>" % esc(poll["question"]))
        if poll["description"]:
            parts.append('<p class="lead">%s</p>' % esc(poll["description"]))
        parts.append(results_block(results, total))
        if voted:
            parts.append(notice("You have already voted in this survey."))
        else:
            parts.append('<p class="actions-row"><a class="button" href="/surveys/%d">Vote in this survey</a></p>' % poll_id)
        parts.append('<p class="actions-row"><a class="button secondary" href="/results">All results</a></p>')
        self.send_page(200, layout("Results: " + poll["question"], "".join(parts), active="results"))

    def create_form_html(self, values, error=None):
        error_html = notice(error, "error") if error else ""
        return (
            "<h1>Create a survey</h1>"
            '<p class="lead">Ask a question and give people the options to choose from.</p>'
            + error_html
            + '<form method="post" action="/create" class="create-form">'
            '<label>Question'
            '<input type="text" name="question" maxlength="%d" required value="%s">'
            "</label>"
            '<label>Description <span class="hint">(optional)</span>'
            '<textarea name="description" rows="3" maxlength="%d">%s</textarea>'
            "</label>"
            '<label>Options <span class="hint">(one per line, at least 2, up to %d)</span>'
            '<textarea name="options" rows="6" required>%s</textarea>'
            "</label>"
            '<button type="submit">Create survey</button>'
            "</form>"
        ) % (
            MAX_QUESTION_LEN, esc(values["question"]),
            MAX_DESCRIPTION_LEN, esc(values["description"]),
            MAX_OPTIONS, esc(values["options"]),
        )

    def page_create_form(self):
        values = {"question": "", "description": "", "options": ""}
        self.send_page(200, layout("Create survey", self.create_form_html(values), active="create"))

    def post_create(self):
        form = self.read_form()
        question = self.field(form, "question").strip()
        description = self.field(form, "description").strip()
        options_raw = self.field(form, "options")
        options = [line.strip() for line in options_raw.splitlines() if line.strip()]
        values = {"question": question, "description": description, "options": options_raw}

        error = None
        if not question:
            error = "Please enter a question."
        elif len(question) > MAX_QUESTION_LEN:
            error = "The question must be at most %d characters." % MAX_QUESTION_LEN
        elif len(description) > MAX_DESCRIPTION_LEN:
            error = "The description must be at most %d characters." % MAX_DESCRIPTION_LEN
        elif len(options) < 2:
            error = "Please enter at least two options, one per line."
        elif len(options) > MAX_OPTIONS:
            error = "A survey can have at most %d options." % MAX_OPTIONS
        elif any(len(o) > MAX_OPTION_LEN for o in options):
            error = "Each option must be at most %d characters." % MAX_OPTION_LEN

        if error:
            return self.send_page(400, layout("Create survey", self.create_form_html(values, error), active="create"))

        with closing(connect()) as conn:
            cur = conn.execute(
                "INSERT INTO polls (question, description, created_at) VALUES (?, ?, ?)",
                (question, description, int(time.time())),
            )
            poll_id = cur.lastrowid
            for position, text in enumerate(options):
                conn.execute(
                    "INSERT INTO options (poll_id, text, position) VALUES (?, ?, ?)",
                    (poll_id, text, position),
                )
            conn.commit()
        self.redirect("/surveys/%d?created=1" % poll_id)


def main():
    init_db()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("Surveys site running at http://127.0.0.1:%d (data: %s)" % (PORT, DATA_DIR), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
