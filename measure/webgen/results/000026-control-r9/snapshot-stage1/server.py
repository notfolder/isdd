#!/usr/bin/env python3
"""Polls website: browse polls, cast votes, and view results.

Standard library only (http.server + sqlite3). Configuration comes from the
environment:
  PORT      port to listen on at 127.0.0.1 (default 8000)
  DATA_DIR  directory for the SQLite database (default ./data)
"""
import html
import os
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR") or BASE_DIR / "data").resolve()
PORT = int(os.environ.get("PORT") or 8000)
DB_PATH = DATA_DIR / "polls.db"
WRITE_LOCK = threading.Lock()
VOTER_COOKIE = "voter_id"
MAX_BODY = 64 * 1024
MAX_QUESTION = 200
MAX_OPTION = 100
MAX_OPTIONS = 10

SAMPLE_POLLS = [
    {
        "question": "What is your favorite programming language?",
        "options": ["Python", "JavaScript", "Go", "Rust"],
        "votes": [14, 11, 5, 8],
    },
    {
        "question": "Which season do you enjoy most?",
        "options": ["Spring", "Summer", "Autumn", "Winter"],
        "votes": [9, 15, 12, 4],
    },
    {
        "question": "Where should the next team offsite be held?",
        "options": ["Kyoto", "Lisbon", "Toronto", "Cape Town", "Reykjavik"],
        "votes": [7, 10, 4, 3, 6],
    },
]

MESSAGES = {
    "created": "Your poll has been created. Share it and start collecting votes.",
    "thanks": "Thank you! Your vote has been recorded.",
    "already": "You have already voted on this poll. The current results are shown below.",
    "invalid": "Please choose one of the options before voting.",
}


class NotFound(Exception):
    pass


# ---------------------------------------------------------------- database

@contextmanager
def db():
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with WRITE_LOCK, db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS polls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
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
                voter_id TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE (poll_id, voter_id)
            );
            """
        )
        if conn.execute("SELECT COUNT(*) FROM polls").fetchone()[0] == 0:
            seed_sample_data(conn)


def seed_sample_data(conn):
    for p_index, sample in enumerate(SAMPLE_POLLS):
        cur = conn.execute("INSERT INTO polls (question) VALUES (?)", (sample["question"],))
        poll_id = cur.lastrowid
        for position, (text, count) in enumerate(zip(sample["options"], sample["votes"])):
            opt = conn.execute(
                "INSERT INTO options (poll_id, text, position) VALUES (?, ?, ?)",
                (poll_id, text, position),
            )
            for n in range(count):
                conn.execute(
                    "INSERT INTO votes (poll_id, option_id, voter_id) VALUES (?, ?, ?)",
                    (poll_id, opt.lastrowid, "sample-%d-%d-%d" % (p_index, position, n)),
                )


def list_polls():
    with db() as conn:
        rows = conn.execute(
            """
            SELECT p.id, p.question,
                   (SELECT COUNT(*) FROM options o WHERE o.poll_id = p.id) AS option_count,
                   (SELECT COUNT(*) FROM votes v WHERE v.poll_id = p.id) AS total_votes
            FROM polls p
            ORDER BY p.id DESC
            """
        ).fetchall()
    return [dict(r) for r in rows]


def get_poll(poll_id):
    with db() as conn:
        row = conn.execute("SELECT id, question FROM polls WHERE id = ?", (poll_id,)).fetchone()
    return dict(row) if row else None


def get_options(poll_id):
    with db() as conn:
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
    return [dict(r) for r in rows]


def has_voted(poll_id, voter_id):
    with db() as conn:
        row = conn.execute(
            "SELECT 1 FROM votes WHERE poll_id = ? AND voter_id = ?", (poll_id, voter_id)
        ).fetchone()
    return row is not None


def cast_vote(poll_id, option_id, voter_id):
    """Returns 'ok', 'duplicate', or 'invalid'."""
    with WRITE_LOCK, db() as conn:
        valid = conn.execute(
            "SELECT 1 FROM options WHERE id = ? AND poll_id = ?", (option_id, poll_id)
        ).fetchone()
        if valid is None:
            return "invalid"
        try:
            conn.execute(
                "INSERT INTO votes (poll_id, option_id, voter_id) VALUES (?, ?, ?)",
                (poll_id, option_id, voter_id),
            )
        except sqlite3.IntegrityError:
            return "duplicate"
    return "ok"


def create_poll_db(question, options):
    with WRITE_LOCK, db() as conn:
        cur = conn.execute("INSERT INTO polls (question) VALUES (?)", (question,))
        poll_id = cur.lastrowid
        for position, text in enumerate(options):
            conn.execute(
                "INSERT INTO options (poll_id, text, position) VALUES (?, ?, ?)",
                (poll_id, text, position),
            )
    return poll_id


# ---------------------------------------------------------------- rendering

def esc(value):
    return html.escape(str(value), quote=True)


def plural(n, word):
    return "%d %s%s" % (n, word, "" if n == 1 else "s")


def first(params, key, default=""):
    values = params.get(key)
    return values[0] if values else default


CSS = """
:root {
  --navy: #000080;
  --navy-dark: #00005c;
  --navy-tint: #e8e8f6;
  --text: #1d1d2b;
  --border: #c9cbe0;
}
* { box-sizing: border-box; }
body {
  margin: 0; min-height: 100vh; display: flex; flex-direction: column;
  background: #ffffff; color: var(--text);
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.5;
}
a { color: var(--navy); }
main { flex: 1; padding: 2rem 0; width: 100%; }
.wrap { width: min(1000px, 92%); margin: 0 auto; }
h1, h2, h3 { color: var(--navy); line-height: 1.25; }
h1 { font-size: 2rem; margin: .3rem 0 .5rem; }
h2 { font-size: 1.4rem; }
h3 { font-size: 1.15rem; margin: 0 0 .4rem; }
.lead { font-size: 1.1rem; color: #333; }
.meta { color: #555; font-size: .92rem; }
.crumbs { font-size: .92rem; margin: 0; }

.site-header { background: var(--navy); color: #fff; }
.header-inner {
  display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: 1rem; padding: .8rem 0;
}
.brand { color: #fff; font-size: 1.5rem; font-weight: 700; text-decoration: none; }
.main-nav { display: flex; flex-wrap: wrap; gap: .3rem; }
.main-nav a {
  color: #fff; text-decoration: none; padding: .4rem .85rem; border-radius: 6px;
}
.main-nav a:hover { background: var(--navy-dark); }
.main-nav a.active { background: #fff; color: var(--navy); font-weight: 600; }

.site-footer { background: var(--navy); color: #fff; padding: 1rem 0; text-align: center; }

.btn {
  display: inline-block; background: var(--navy); color: #fff;
  border: 2px solid var(--navy); border-radius: 6px; padding: .5rem 1.1rem;
  font: inherit; font-weight: 600; text-decoration: none; cursor: pointer;
}
.btn:hover { background: var(--navy-dark); border-color: var(--navy-dark); }
.btn-outline { background: #fff; color: var(--navy); }
.btn-outline:hover { background: var(--navy-tint); color: var(--navy-dark); }
.actions { display: flex; gap: .6rem; flex-wrap: wrap; margin-top: 1rem; }

.card {
  border: 2px solid var(--navy); border-radius: 10px; padding: 1.2rem 1.4rem;
  background: #fff;
}
.hero { margin-bottom: 1rem; }
.grid { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); }
.notice {
  border-left: 6px solid var(--navy); background: var(--navy-tint);
  padding: .8rem 1rem; border-radius: 6px; margin: 1rem 0;
}
.badge {
  display: inline-block; background: var(--navy); color: #fff; border-radius: 999px;
  font-size: .75rem; padding: .05rem .55rem; margin-left: .4rem; vertical-align: middle;
}

.options { list-style: none; padding: 0; margin: 1rem 0; display: grid; gap: .6rem; }
.option-label {
  display: flex; align-items: center; gap: .7rem; cursor: pointer;
  border: 2px solid var(--navy); border-radius: 8px; padding: .7rem 1rem;
}
.option-label:hover { background: var(--navy-tint); }
.option-label input { width: 1.1rem; height: 1.1rem; accent-color: var(--navy); }

.bar-row { margin: 1.1rem 0; }
.bar-head { display: flex; justify-content: space-between; gap: 1rem; font-weight: 600; }
.bar-track {
  background: var(--navy-tint); border: 1px solid var(--navy); border-radius: 999px;
  height: 1.1rem; overflow: hidden; margin-top: .35rem;
}
.bar-fill { background: var(--navy); height: 100%; }

table { width: 100%; border-collapse: collapse; background: #fff; }
th, td { text-align: left; padding: .7rem .8rem; border-bottom: 1px solid var(--border); }
th { background: var(--navy); color: #fff; }

form label { display: block; font-weight: 600; margin-top: 1rem; }
input[type=text], textarea {
  width: 100%; padding: .6rem .7rem; border: 2px solid var(--navy);
  border-radius: 6px; font: inherit; margin-top: .3rem; background: #fff;
}
textarea { min-height: 10rem; resize: vertical; }
.errors { border-left-color: var(--navy-dark); }
.errors ul { margin: .3rem 0 0 1.2rem; padding: 0; }
"""


def nav_html(active):
    items = [
        ("home", "/", "Home"),
        ("browse", "/polls", "Browse Polls"),
        ("results", "/results", "Results"),
        ("create", "/polls/new", "Create Poll"),
    ]
    parts = []
    for key, href, label in items:
        cls = ' class="active"' if key == active else ""
        parts.append('<a href="%s"%s>%s</a>' % (href, cls, label))
    return "\n".join(parts)


def layout(title, active, content):
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s | Polls</title>
<style>%(css)s</style>
</head>
<body>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="/">Polls</a>
    <nav class="main-nav" aria-label="Main navigation">
%(nav)s
    </nav>
  </div>
</header>
<main class="wrap">
%(content)s
</main>
<footer class="site-footer">
  <div class="wrap">Polls &mdash; cast your vote and see what everyone thinks.</div>
</footer>
</body>
</html>
""" % {"title": esc(title), "css": CSS, "nav": nav_html(active), "content": content}


def message_html(params):
    key = first(params, "msg")
    if key not in MESSAGES:
        return ""
    return '<p class="notice" role="status">%s</p>' % esc(MESSAGES[key])


def poll_cards(polls):
    if not polls:
        return ('<div class="notice">No polls yet. '
                '<a href="/polls/new">Create the first one</a>.</div>')
    cards = []
    for p in polls:
        cards.append(
            '<article class="card">'
            '<h3><a href="/polls/%(id)d">%(question)s</a></h3>'
            '<p class="meta">%(options)s &middot; %(votes)s</p>'
            '<div class="actions">'
            '<a class="btn" href="/polls/%(id)d">Vote</a>'
            '<a class="btn btn-outline" href="/polls/%(id)d/results">View results</a>'
            "</div></article>"
            % {
                "id": p["id"],
                "question": esc(p["question"]),
                "options": plural(p["option_count"], "option"),
                "votes": plural(p["total_votes"], "vote"),
            }
        )
    return '<div class="grid">%s</div>' % "".join(cards)


def new_poll_form(question="", options_text="", errors=None):
    error_block = ""
    if errors:
        items = "".join("<li>%s</li>" % esc(e) for e in errors)
        error_block = '<div class="notice errors" role="alert"><strong>Please fix the following:</strong><ul>%s</ul></div>' % items
    return """
<p class="crumbs"><a href="/">Home</a> &rsaquo; Create Poll</p>
<h1>Create a poll</h1>
<p class="lead">Ask a question and give people at least two options to choose from.</p>
%(errors)s
<form method="post" action="/polls/new" class="card">
  <label for="question">Question</label>
  <input type="text" id="question" name="question" maxlength="%(max_q)d" required value="%(question)s">
  <label for="options">Options (one per line, 2 to %(max_o)d)</label>
  <textarea id="options" name="options" required>%(options)s</textarea>
  <div class="actions">
    <button class="btn" type="submit">Create poll</button>
    <a class="btn btn-outline" href="/polls">Cancel</a>
  </div>
</form>
""" % {
        "errors": error_block,
        "max_q": MAX_QUESTION,
        "max_o": MAX_OPTIONS,
        "question": esc(question),
        "options": esc(options_text),
    }


# ---------------------------------------------------------------- HTTP

class Handler(BaseHTTPRequestHandler):
    server_version = "PollsSite/1.0"

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)

    # --- request plumbing
    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    def dispatch(self, method):
        self.cookie_headers = []
        try:
            self.ensure_voter()
            parsed = urlparse(self.path)
            parts = [p for p in parsed.path.split("/") if p]
            params = parse_qs(parsed.query, keep_blank_values=True)
            if method == "GET":
                self.route_get(parts, params)
            else:
                self.route_post(parts)
        except NotFound:
            self.send_html(404, layout("Not found", "", self.not_found_html()))
        except Exception as exc:  # keep the server alive, report the failure
            print("Error handling %s %s: %r" % (method, self.path, exc), flush=True)
            self.send_html(500, layout("Server error", "", "<h1>Something went wrong</h1>"
                                       '<p class="lead">Please try again.</p>'))

    def ensure_voter(self):
        jar = cookies.SimpleCookie()
        try:
            jar.load(self.headers.get("Cookie", ""))
        except cookies.CookieError:
            pass
        morsel = jar.get(VOTER_COOKIE)
        self.voter_id = morsel.value if morsel and 0 < len(morsel.value) <= 64 else ""
        if not self.voter_id:
            self.voter_id = uuid.uuid4().hex
            self.cookie_headers.append(
                "%s=%s; Path=/; Max-Age=31536000; HttpOnly; SameSite=Lax" % (VOTER_COOKIE, self.voter_id)
            )

    def read_form(self):
        length = min(int(self.headers.get("Content-Length") or 0), MAX_BODY)
        body = self.rfile.read(length).decode("utf-8", "replace")
        return parse_qs(body, keep_blank_values=True)

    def send_common_headers(self, status):
        self.send_response(status)
        for value in self.cookie_headers:
            self.send_header("Set-Cookie", value)

    def send_html(self, status, text):
        data = text.encode("utf-8")
        self.send_common_headers(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, location):
        self.send_common_headers(303)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def not_found_html(self):
        return ('<h1>Page not found</h1><p class="lead">The page you asked for does not exist.</p>'
                '<div class="actions"><a class="btn" href="/">Go to home</a>'
                '<a class="btn btn-outline" href="/polls">Browse polls</a></div>')

    # --- routing
    def route_get(self, parts, params):
        if not parts:
            return self.page_home()
        if parts == ["polls"]:
            return self.page_browse()
        if parts == ["polls", "new"]:
            return self.page_new_poll()
        if parts == ["results"]:
            return self.page_all_results()
        if len(parts) >= 2 and parts[0] == "polls" and parts[1].isdigit():
            poll_id = int(parts[1])
            if len(parts) == 2:
                return self.page_poll(poll_id, params)
            if parts[2:] == ["results"]:
                return self.page_poll_results(poll_id, params)
        raise NotFound()

    def route_post(self, parts):
        if parts == ["polls", "new"]:
            return self.submit_new_poll()
        if len(parts) == 3 and parts[0] == "polls" and parts[1].isdigit() and parts[2] == "vote":
            return self.submit_vote(int(parts[1]))
        raise NotFound()

    # --- pages
    def page_home(self):
        polls = list_polls()[:3]
        content = """
<section class="card hero">
  <h1>Welcome to Polls</h1>
  <p class="lead">Browse open polls, cast your vote in one click, and see the results as they grow.</p>
  <div class="actions">
    <a class="btn" href="/polls">Browse polls</a>
    <a class="btn btn-outline" href="/results">View results</a>
    <a class="btn btn-outline" href="/polls/new">Create a poll</a>
  </div>
</section>
<h2>Latest polls</h2>
%s
""" % poll_cards(polls)
        self.send_html(200, layout("Home", "home", content))

    def page_browse(self):
        content = """
<h1>Browse polls</h1>
<p class="lead">Pick a poll, choose an option, and cast your vote. You can vote once per poll.</p>
%s
""" % poll_cards(list_polls())
        self.send_html(200, layout("Browse Polls", "browse", content))

    def page_new_poll(self):
        self.send_html(200, layout("Create Poll", "create", new_poll_form()))

    def page_poll(self, poll_id, params):
        poll = get_poll(poll_id)
        if poll is None:
            raise NotFound()
        options = get_options(poll_id)
        voted = has_voted(poll_id, self.voter_id)
        if voted:
            body = (
                '<p class="notice">You have already voted on this poll. Thank you for taking part!</p>'
                '<div class="actions">'
                '<a class="btn" href="/polls/%d/results">View results</a>'
                '<a class="btn btn-outline" href="/polls">Back to all polls</a></div>' % poll_id
            )
        else:
            items = []
            for opt in options:
                items.append(
                    '<li><label class="option-label">'
                    '<input type="radio" name="option_id" value="%d" required>'
                    "<span>%s</span></label></li>" % (opt["id"], esc(opt["text"]))
                )
            body = (
                '<form method="post" action="/polls/%d/vote">'
                '<ul class="options">%s</ul>'
                '<div class="actions">'
                '<button class="btn" type="submit">Cast vote</button>'
                '<a class="btn btn-outline" href="/polls/%d/results">View results</a>'
                "</div></form>" % (poll_id, "".join(items), poll_id)
            )
        content = """
<p class="crumbs"><a href="/polls">All polls</a> &rsaquo; Poll #%(id)d</p>
<h1>%(question)s</h1>
<p class="lead">%(hint)s</p>
%(msg)s
%(body)s
""" % {
            "id": poll_id,
            "question": esc(poll["question"]),
            "hint": "Choose one option and cast your vote." if not voted else
                    "Your vote is in. Here is how everyone else voted.",
            "msg": message_html(params),
            "body": body,
        }
        self.send_html(200, layout(poll["question"], "browse", content))

    def page_poll_results(self, poll_id, params):
        poll = get_poll(poll_id)
        if poll is None:
            raise NotFound()
        options = get_options(poll_id)
        total = sum(o["votes"] for o in options)
        leader = max((o["votes"] for o in options), default=0)
        rows = []
        for opt in options:
            pct = opt["votes"] * 100.0 / total if total else 0.0
            badge = '<span class="badge">Leading</span>' if total and opt["votes"] == leader else ""
            rows.append(
                '<div class="bar-row">'
                '<div class="bar-head"><span>%s%s</span><span>%d (%.1f%%)</span></div>'
                '<div class="bar-track"><div class="bar-fill" style="width:%.1f%%"></div></div>'
                "</div>" % (esc(opt["text"]), badge, opt["votes"], pct, pct)
            )
        voted = has_voted(poll_id, self.voter_id)
        if voted:
            action = '<p class="meta">You have voted on this poll.</p>'
        else:
            action = '<a class="btn" href="/polls/%d">Vote on this poll</a>' % poll_id
        content = """
<p class="crumbs"><a href="/polls">All polls</a> &rsaquo; <a href="/polls/%(id)d">Poll #%(id)d</a> &rsaquo; Results</p>
<h1>%(question)s</h1>
<p class="lead">Total votes: <strong>%(total)d</strong></p>
%(msg)s
<section class="card">
%(rows)s
</section>
<div class="actions">%(action)s<a class="btn btn-outline" href="/results">All results</a></div>
""" % {
            "id": poll_id,
            "question": esc(poll["question"]),
            "total": total,
            "msg": message_html(params),
            "rows": "".join(rows) if rows else '<p class="meta">This poll has no options.</p>',
            "action": action,
        }
        self.send_html(200, layout("Results: " + poll["question"], "results", content))

    def page_all_results(self):
        rows = []
        for p in list_polls():
            options = get_options(p["id"])
            total = sum(o["votes"] for o in options)
            if total:
                leader = max(options, key=lambda o: o["votes"])["text"]
                leader_html = "%s" % esc(leader)
            else:
                leader_html = '<span class="meta">No votes yet</span>'
            rows.append(
                "<tr><td>%s</td><td>%d</td><td>%s</td>"
                '<td><a href="/polls/%d/results">View results</a></td></tr>'
                % (esc(p["question"]), total, leader_html, p["id"])
            )
        if rows:
            table = ("<table><thead><tr><th>Poll</th><th>Total votes</th>"
                     "<th>Leading option</th><th></th></tr></thead><tbody>%s</tbody></table>"
                     % "".join(rows))
        else:
            table = '<div class="notice">No polls yet. <a href="/polls/new">Create the first one</a>.</div>'
        content = """
<h1>Results</h1>
<p class="lead">A summary of every poll. Open a poll to see the full breakdown.</p>
%s
""" % table
        self.send_html(200, layout("Results", "results", content))

    # --- actions
    def submit_vote(self, poll_id):
        if get_poll(poll_id) is None:
            raise NotFound()
        form = self.read_form()
        try:
            option_id = int(first(form, "option_id", "x"))
        except ValueError:
            return self.redirect("/polls/%d?msg=invalid" % poll_id)
        result = cast_vote(poll_id, option_id, self.voter_id)
        if result == "ok":
            self.redirect("/polls/%d/results?msg=thanks" % poll_id)
        elif result == "duplicate":
            self.redirect("/polls/%d/results?msg=already" % poll_id)
        else:
            self.redirect("/polls/%d?msg=invalid" % poll_id)

    def submit_new_poll(self):
        form = self.read_form()
        question = first(form, "question").strip()
        raw_options = first(form, "options")
        options = []
        seen = set()
        for line in raw_options.splitlines():
            text = line.strip()
            if text and text.lower() not in seen:
                seen.add(text.lower())
                options.append(text)
        errors = []
        if not question:
            errors.append("Please enter a question.")
        elif len(question) > MAX_QUESTION:
            errors.append("The question must be %d characters or fewer." % MAX_QUESTION)
        if len(options) < 2:
            errors.append("Please enter at least two different options (one per line).")
        if len(options) > MAX_OPTIONS:
            errors.append("You can add up to %d options." % MAX_OPTIONS)
        if any(len(o) > MAX_OPTION for o in options):
            errors.append("Each option must be %d characters or fewer." % MAX_OPTION)
        if errors:
            body = layout("Create Poll", "create",
                          new_poll_form(question, raw_options, errors))
            return self.send_html(400, body)
        poll_id = create_poll_db(question, options)
        self.redirect("/polls/%d?msg=created" % poll_id)


def main():
    init_db()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("Polls site running at http://127.0.0.1:%d (data: %s)" % (PORT, DATA_DIR), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
