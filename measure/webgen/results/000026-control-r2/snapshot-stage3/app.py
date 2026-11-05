#!/usr/bin/env python3
"""Surveys website: browse surveys, cast a vote, and view results.

Standard library only (http.server + sqlite3). Configuration via environment:
  PORT      - TCP port on 127.0.0.1 (default 8000)
  DATA_DIR  - directory for the SQLite database (default ./data)
"""
import html
import os
import re
import sqlite3
import sys
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PORT = int(os.environ.get("PORT", "8000"))
VOTE_LOCK = threading.Lock()
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data"
)
DB_PATH = os.path.join(DATA_DIR, "polls.db")

# Cookie remembering which option this browser voted for in each survey.
# Format: "<poll_id>-<option_id>.<poll_id>-<option_id>..."
VOTE_COOKIE = "poll_votes"

SCHEMA = """
CREATE TABLE IF NOT EXISTS polls (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS options (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id  INTEGER NOT NULL REFERENCES polls(id) ON DELETE CASCADE,
    label    TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS votes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id    INTEGER NOT NULL REFERENCES polls(id) ON DELETE CASCADE,
    option_id  INTEGER NOT NULL REFERENCES options(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL
);
"""

# Sample content used only when the database is empty (first start).
# Each option is (label, number of seeded votes).
SAMPLE_POLLS = [
    {
        "title": "Favorite programming language",
        "description": "Which language would you most like to use for your next project?",
        "options": [("Python", 42), ("TypeScript", 35), ("Rust", 27), ("Go", 18)],
    },
    {
        "title": "Best season of the year",
        "description": "When do you enjoy being outdoors the most?",
        "options": [("Spring", 14), ("Summer", 22), ("Autumn", 31), ("Winter", 9)],
    },
    {
        "title": "Team lunch spot",
        "description": "Where should we go for the next team lunch?",
        "options": [
            ("Ramen shop", 8),
            ("Italian bistro", 5),
            ("Food truck park", 11),
            ("Bring your own", 2),
        ],
    },
    {
        "title": "Weekend plan",
        "description": "What would you rather do this Saturday?",
        "options": [("Hiking", 0), ("Movie marathon", 0), ("Board games", 0)],
    },
]

ROUTE_POLL = re.compile(r"^/surveys/(\d{1,12})$")
ROUTE_RESULTS = re.compile(r"^/surveys/(\d{1,12})/results$")
ROUTE_VOTE = re.compile(r"^/surveys/(\d{1,12})/vote$")
ROUTE_LEGACY = re.compile(r"^/polls/(\d{1,12})(/results)?$")  # old URLs -> new ones


def esc(value):
    return html.escape(str(value), quote=True)


def plural(count, word):
    return "%d %s" % (count, word if count == 1 else word + "s")


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------- database

@contextmanager
def tx():
    """Yield a connection; commit on success, roll back on error."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
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


def seed_if_empty(conn):
    (count,) = conn.execute("SELECT COUNT(*) FROM polls").fetchone()
    if count:
        return
    now = now_iso()
    for poll in SAMPLE_POLLS:
        poll_id = conn.execute(
            "INSERT INTO polls (title, description, created_at) VALUES (?, ?, ?)",
            (poll["title"], poll["description"], now),
        ).lastrowid
        for position, (label, seeded_votes) in enumerate(poll["options"]):
            option_id = conn.execute(
                "INSERT INTO options (poll_id, label, position) VALUES (?, ?, ?)",
                (poll_id, label, position),
            ).lastrowid
            if seeded_votes:
                conn.executemany(
                    "INSERT INTO votes (poll_id, option_id, created_at) VALUES (?, ?, ?)",
                    [(poll_id, option_id, now)] * seeded_votes,
                )


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    with tx() as conn:
        conn.executescript(SCHEMA)
        seed_if_empty(conn)


def list_polls(conn):
    return conn.execute(
        """
        SELECT p.id, p.title, p.description,
               (SELECT COUNT(*) FROM votes v WHERE v.poll_id = p.id) AS total_votes,
               (SELECT COUNT(*) FROM options o WHERE o.poll_id = p.id) AS option_count
        FROM polls p
        ORDER BY p.id
        """
    ).fetchall()


def get_poll(conn, poll_id):
    return conn.execute(
        "SELECT id, title, description FROM polls WHERE id = ?", (poll_id,)
    ).fetchone()


def get_options(conn, poll_id):
    return conn.execute(
        "SELECT id, label FROM options WHERE poll_id = ? ORDER BY position, id",
        (poll_id,),
    ).fetchall()


def poll_results(conn, poll_id):
    """Return (total_votes, [ {id, label, votes, percent}, ... ]) for a poll."""
    rows = conn.execute(
        """
        SELECT o.id, o.label, COUNT(v.id) AS votes
        FROM options o
        LEFT JOIN votes v ON v.option_id = o.id
        WHERE o.poll_id = ?
        GROUP BY o.id, o.label, o.position
        ORDER BY o.position, o.id
        """,
        (poll_id,),
    ).fetchall()
    total = sum(r["votes"] for r in rows)
    results = [
        {
            "id": r["id"],
            "label": r["label"],
            "votes": r["votes"],
            "percent": (r["votes"] * 100.0 / total) if total else 0.0,
        }
        for r in rows
    ]
    return total, results


def leader_label(results):
    best = None
    for item in results:
        if item["votes"] > 0 and (best is None or item["votes"] > best["votes"]):
            best = item
    return best["label"] if best else "No votes yet"


# ---------------------------------------------------------------- cookies

def read_votes(headers):
    """Return {poll_id: option_id} for votes cast from this browser."""
    votes = {}
    for part in headers.get("Cookie", "").split(";"):
        name, _, value = part.strip().partition("=")
        if name != VOTE_COOKIE:
            continue
        for item in value.split("."):
            poll_part, _, option_part = item.partition("-")
            if poll_part.isdigit() and option_part.isdigit():
                votes[int(poll_part)] = int(option_part)
    return votes


def vote_cookie_header(votes):
    value = ".".join("%d-%d" % (p, o) for p, o in sorted(votes.items()))
    return (
        "Set-Cookie",
        "%s=%s; Path=/; Max-Age=31536000; SameSite=Lax" % (VOTE_COOKIE, value),
    )


# ---------------------------------------------------------------- layout

NAV_ITEMS = [("/", "Surveys", "surveys"), ("/results", "Results", "results")]

STYLE = """
:root { --yellow: #ffffe0; --slate: #2f4f4f; --slate-dark: #243c3c; --slate-light: #f2f2c2; --text: #1d2a2a; }
* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; display: flex; flex-direction: column;
       font-family: system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
       background: var(--yellow); color: var(--text); line-height: 1.5; }
a { color: var(--slate); }
.site-header { background: var(--slate); color: #fff; }
.site-header .inner { max-width: 960px; margin: 0 auto; padding: 10px 20px;
       display: flex; align-items: center; justify-content: space-between;
       flex-wrap: wrap; gap: 12px; }
.brand { color: #fff; font-size: 1.4rem; font-weight: 700; text-decoration: none; }
nav.main-nav { display: flex; gap: 6px; flex-wrap: wrap; }
nav.main-nav a { color: #fff; text-decoration: none; padding: 8px 14px;
       border-radius: 6px; font-weight: 600; border: 2px solid transparent; }
nav.main-nav a:hover { background: var(--slate-dark); }
nav.main-nav a.active { background: var(--yellow); color: var(--slate); }
main { max-width: 960px; margin: 0 auto; padding: 32px 20px; width: 100%; flex: 1; }
h1 { color: var(--slate); margin: 0 0 8px; font-size: 2rem; }
h2 { color: var(--slate); font-size: 1.3rem; margin: 0; }
.lead { color: #3a3a55; margin: 0 0 16px; }
.breadcrumb { font-size: .95rem; margin-bottom: 12px; color: var(--slate); }
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
       gap: 20px; margin-top: 24px; }
.card { border: 2px solid var(--slate); border-radius: 10px; padding: 20px; background: var(--yellow);
       display: flex; flex-direction: column; gap: 10px; }
.card p { margin: 0; color: #2a2a40; }
.meta { font-size: .95rem; color: var(--slate); font-weight: 600; }
.badge { display: inline-block; background: var(--slate); color: #fff; border-radius: 999px;
       padding: 2px 12px; font-size: .85rem; font-weight: 600; }
.btn { display: inline-block; background: var(--slate); color: #fff; border: 2px solid var(--slate);
       border-radius: 6px; padding: 10px 18px; font-size: 1rem; font-weight: 600;
       text-decoration: none; cursor: pointer; font-family: inherit; }
.btn:hover { background: var(--slate-dark); border-color: var(--slate-dark); }
.btn:disabled, .btn[aria-disabled="true"] { opacity: .5; cursor: not-allowed; }
.btn:disabled:hover, .btn[aria-disabled="true"]:hover { background: var(--slate); border-color: var(--slate); }
.option-label.disabled { opacity: .6; cursor: not-allowed; }
.option-label.disabled:hover { background: var(--yellow); }
.btn-outline { background: var(--yellow); color: var(--slate); }
.btn-outline:hover { background: var(--slate-light); color: var(--slate); }
.actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: auto; }
.options { list-style: none; padding: 0; margin: 20px 0; display: flex; flex-direction: column; gap: 12px; }
.option-label { display: flex; align-items: center; gap: 12px; border: 2px solid var(--slate);
       border-radius: 8px; padding: 14px 16px; cursor: pointer; background: var(--yellow); font-size: 1.05rem; }
.option-label:hover { background: var(--slate-light); }
.option-label input { width: 20px; height: 20px; accent-color: var(--slate); margin: 0; }
.notice { border-left: 6px solid var(--slate); background: var(--slate-light);
       padding: 12px 16px; border-radius: 6px; margin: 16px 0; color: var(--slate-dark); }
.summary { display: flex; gap: 16px; flex-wrap: wrap; margin: 20px 0; }
.stat { border: 2px solid var(--slate); border-radius: 8px; padding: 12px 18px; min-width: 180px; }
.stat span { color: var(--slate); font-weight: 600; font-size: .95rem; }
.stat strong { display: block; font-size: 1.5rem; color: var(--slate); }
.result-row { margin: 18px 0; }
.result-head { display: flex; justify-content: space-between; align-items: center;
       gap: 12px; font-weight: 600; color: var(--slate); flex-wrap: wrap; }
.bar { background: var(--yellow); border: 2px solid var(--slate); border-radius: 6px; height: 30px;
       overflow: hidden; margin-top: 6px; }
.bar-fill { background: var(--slate); height: 100%; }
.empty { color: #4a4a66; font-style: italic; }
.overview-item { display: flex; flex-direction: column; gap: 10px; }
.site-footer { border-top: 2px solid var(--slate); color: var(--slate); text-align: center;
       padding: 16px; font-size: .9rem; }
"""


def layout(title, content, active=""):
    links = []
    for href, label, key in NAV_ITEMS:
        cls = ' class="active"' if key == active else ""
        links.append('<a href="%s"%s>%s</a>' % (href, cls, label))
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<style>%(style)s</style>
</head>
<body>
<header class="site-header">
  <div class="inner">
    <a class="brand" href="/">Surveys</a>
    <nav class="main-nav" aria-label="Main navigation">%(nav)s</nav>
  </div>
</header>
<main>
%(content)s
</main>
<footer class="site-footer">Surveys &middot; Vote and see the results</footer>
</body>
</html>
""" % {
        "title": esc(title if title == "Surveys" else title + " | Surveys"),
        "style": STYLE,
        "nav": "".join(links),
        "content": content,
    }


def not_found_content(message):
    return """<h1>Page not found</h1>
<p class="lead">%s</p>
<p><a class="btn" href="/">Back to all surveys</a></p>""" % esc(message)


# ---------------------------------------------------------------- server

class Handler(BaseHTTPRequestHandler):
    server_version = "SurveysSite/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")

    def route(self, method):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if method == "GET":
            if path == "/":
                return self.page_home()
            if path == "/polls":
                return self.redirect("/")
            match = ROUTE_LEGACY.match(path)
            if match:
                return self.redirect("/surveys/%s%s" % (match.group(1), match.group(2) or ""))
            if path == "/results":
                return self.page_all_results()
            match = ROUTE_RESULTS.match(path)
            if match:
                return self.page_poll_results(int(match.group(1)))
            match = ROUTE_POLL.match(path)
            if match:
                return self.page_poll_vote(int(match.group(1)))
        elif method == "POST":
            match = ROUTE_VOTE.match(path)
            if match:
                return self.handle_vote(int(match.group(1)))
        self.send_html(404, layout("Not found", not_found_content("That page does not exist.")))

    # -- helpers
    def send_html(self, status, body, extra_headers=()):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        for name, value in extra_headers:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, location, extra_headers=()):
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        for name, value in extra_headers:
            self.send_header(name, value)
        self.end_headers()

    # -- pages
    def page_home(self):
        with tx() as conn:
            polls = list_polls(conn)
        votes = read_votes(self.headers)
        cards = []
        for p in polls:
            pid = p["id"]
            if pid in votes:
                badge = '<span class="badge">You have already voted</span>'
                buttons = (
                    '<button class="btn" type="button" disabled>Vote now</button>'
                    '<a class="btn btn-outline" href="/surveys/%d/results">View results</a>'
                ) % pid
            else:
                badge = ""
                buttons = (
                    '<a class="btn" href="/surveys/%d">Vote now</a>'
                    '<a class="btn btn-outline" href="/surveys/%d/results">View results</a>'
                ) % (pid, pid)
            cards.append(
                """<article class="card">
  <h2>%(title)s</h2>
  <p>%(desc)s</p>
  <div class="meta">%(total)s &middot; %(options)d options</div>
  <div>%(badge)s</div>
  <div class="actions">%(buttons)s</div>
</article>""" % {
                    "title": esc(p["title"]),
                    "desc": esc(p["description"]),
                    "total": plural(p["total_votes"], "vote"),
                    "options": p["option_count"],
                    "badge": badge,
                    "buttons": buttons,
                }
            )
        content = (
            "<h1>Surveys</h1>\n"
            '<p class="lead">Browse the surveys below, cast your vote for one option, '
            "and see how everyone else voted.</p>\n"
            '<div class="card-grid">\n%s\n</div>' % "\n".join(cards)
            if cards
            else "<h1>Surveys</h1>\n<p class=\"empty\">There are no surveys yet.</p>"
        )
        self.send_html(200, layout("Surveys", content, active="surveys"))

    def page_poll_vote(self, poll_id):
        with tx() as conn:
            poll = get_poll(conn, poll_id)
            options = get_options(conn, poll_id) if poll else []
        if poll is None:
            return self.send_html(404, layout("Not found", not_found_content("This survey does not exist.")))
        my_option = read_votes(self.headers).get(poll_id)
        already_voted = my_option is not None

        items = "\n".join(
            '    <li><label class="option-label%(cls)s"><input type="radio" name="option" value="%(oid)d"%(attrs)s>'
            "<span>%(label)s</span></label></li>" % {
                "cls": " disabled" if already_voted else "",
                "oid": o["id"],
                "attrs": (" disabled" + (" checked" if o["id"] == my_option else ""))
                if already_voted else " required",
                "label": esc(o["label"]),
            }
            for o in options
        )
        if already_voted:
            notice = (
                '<div class="notice">You have already voted in this survey. '
                'Each browser can vote once per survey.</div>'
            )
            submit = '<button class="btn" type="submit" disabled>Cast my vote</button>'
        else:
            notice = ""
            submit = '<button class="btn" type="submit">Cast my vote</button>'
        content = """<div class="breadcrumb"><a href="/">Surveys</a> / %(title)s</div>
<h1>%(title)s</h1>
<p class="lead">%(desc)s</p>
%(notice)s
<form method="post" action="/surveys/%(pid)d/vote">
  <ul class="options">
%(items)s
  </ul>
  <div class="actions">
    %(submit)s
    <a class="btn btn-outline" href="/surveys/%(pid)d/results">See results</a>
  </div>
</form>""" % {
            "title": esc(poll["title"]),
            "desc": esc(poll["description"]),
            "pid": poll_id,
            "items": items,
            "notice": notice,
            "submit": submit,
        }
        self.send_html(200, layout(poll["title"], content, active="surveys"))

    def page_poll_results(self, poll_id):
        with tx() as conn:
            poll = get_poll(conn, poll_id)
            if poll is None:
                total, results = 0, []
            else:
                total, results = poll_results(conn, poll_id)
        if poll is None:
            return self.send_html(404, layout("Not found", not_found_content("This survey does not exist.")))

        my_option = read_votes(self.headers).get(poll_id)
        my_label = None
        rows = []
        for item in results:
            mine = item["id"] == my_option
            if mine:
                my_label = item["label"]
            tag = ' <span class="badge">Your vote</span>' if mine else ""
            rows.append(
                """<div class="result-row">
  <div class="result-head"><span>%(label)s%(tag)s</span><span>%(votes_text)s &middot; %(pct)d%%</span></div>
  <div class="bar" role="img" aria-label="%(label)s: %(pct)d percent"><div class="bar-fill" style="width: %(width).2f%%"></div></div>
</div>""" % {
                    "label": esc(item["label"]),
                    "tag": tag,
                    "votes_text": plural(item["votes"], "vote"),
                    "pct": round(item["percent"]),
                    "width": item["percent"],
                }
            )

        if my_option is not None:
            notice = '<div class="notice">Thank you for voting! You voted for <strong>%s</strong>.</div>' % esc(
                my_label or "an option"
            )
        else:
            notice = (
                '<div class="notice">You have not voted in this survey yet. '
                '<a class="btn" href="/surveys/%d">Vote now</a></div>' % poll_id
            )

        body_rows = "\n".join(rows) if total else '<p class="empty">No votes yet. Be the first to vote!</p>'
        content = """<div class="breadcrumb"><a href="/">Surveys</a> / <a href="/results">Results</a> / %(title)s</div>
<h1>%(title)s</h1>
<p class="lead">%(desc)s</p>
%(notice)s
<div class="summary">
  <div class="stat"><span>Total votes</span><strong>%(total)d</strong></div>
  <div class="stat"><span>Leading option</span><strong>%(leader)s</strong></div>
</div>
%(rows)s""" % {
            "title": esc(poll["title"]),
            "desc": esc(poll["description"]),
            "notice": notice,
            "total": total,
            "leader": esc(leader_label(results)),
            "rows": body_rows,
        }
        self.send_html(200, layout(poll["title"] + " results", content, active="results"))

    def page_all_results(self):
        with tx() as conn:
            polls = list_polls(conn)
            summaries = []
            for p in polls:
                total, results = poll_results(conn, p["id"])
                summaries.append((p, total, leader_label(results)))
        votes = read_votes(self.headers)
        cards = []
        for p, total, leader in summaries:
            pid = p["id"]
            voted = " <span class=\"badge\">You voted</span>" if pid in votes else ""
            cards.append(
                """<article class="card overview-item">
  <h2>%(title)s%(voted)s</h2>
  <div class="meta">%(total)s &middot; Leading: %(leader)s</div>
  <div class="actions"><a class="btn" href="/surveys/%(pid)d/results">View results</a></div>
</article>""" % {
                    "title": esc(p["title"]),
                    "voted": voted,
                    "total": plural(total, "vote"),
                    "leader": esc(leader),
                    "pid": pid,
                }
            )
        content = (
            "<h1>Results</h1>\n"
            '<p class="lead">Current standings for every survey.</p>\n'
            '<div class="card-grid">\n%s\n</div>' % "\n".join(cards)
            if cards
            else "<h1>Results</h1>\n<p class=\"empty\">There are no surveys yet.</p>"
        )
        self.send_html(200, layout("Results", content, active="results"))

    # -- actions
    def handle_vote(self, poll_id):
        length = int(self.headers.get("Content-Length") or 0)
        form = parse_qs(self.rfile.read(length).decode("utf-8", "replace"))
        raw_option = (form.get("option") or [""])[0].strip()

        error = None
        votes = read_votes(self.headers)
        already_voted = False
        # Serialize check-and-insert so concurrent POSTs cannot both pass the check.
        with VOTE_LOCK, tx() as conn:
            poll = get_poll(conn, poll_id)
            if poll is None:
                error = ("This survey does not exist.", 404)
            else:
                if poll_id in votes:
                    # Already voted from this browser: do not record a second vote.
                    already_voted = True
                elif not raw_option.isdigit():
                    error = ("Please choose one option before voting.", 400)
                else:
                    option = conn.execute(
                        "SELECT id FROM options WHERE id = ? AND poll_id = ?",
                        (int(raw_option), poll_id),
                    ).fetchone()
                    if option is None:
                        error = ("That option is not part of this survey.", 400)
                    else:
                        conn.execute(
                            "INSERT INTO votes (poll_id, option_id, created_at) VALUES (?, ?, ?)",
                            (poll_id, option["id"], now_iso()),
                        )
                        votes[poll_id] = option["id"]

        if error:
            message, code = error
            back = ""
            if poll_id and code != 404:
                back = '<p><a class="btn btn-outline" href="/surveys/%d">Back to the survey</a></p>' % poll_id
            content = "<h1>Vote not recorded</h1>\n<p class=\"lead\">%s</p>\n%s" % (esc(message), back)
            return self.send_html(code, layout("Vote not recorded", content, active="surveys"))

        if already_voted:
            # Show the survey page, which displays "You have already voted" with disabled controls.
            return self.redirect("/surveys/%d" % poll_id)

        cookie = vote_cookie_header(votes)
        self.redirect("/surveys/%d/results" % poll_id, [cookie])


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
