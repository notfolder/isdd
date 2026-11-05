#!/usr/bin/env python3
"""Surveys website: browse surveys, cast a vote, and view results.

Standard library only (http.server + sqlite3). Configured via environment:
  PORT      port to listen on (default 8000), bound to 127.0.0.1
  DATA_DIR  directory for the SQLite database (default ./data)
"""
import html
import os
import re
import sqlite3
import urllib.parse
import uuid
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(BASE_DIR, "data")
PORT = int(os.environ.get("PORT") or "8000")
DB_PATH = os.path.join(DATA_DIR, "polls.db")

MAX_TITLE = 200
MAX_OPTION = 100
MAX_OPTIONS = 20

SAMPLE_POLLS = [
    {
        "title": "Favorite programming language",
        "description": "Which language do you reach for first when starting a new project?",
        "options": ["Python", "JavaScript", "Rust", "Go", "Other"],
    },
    {
        "title": "Where should we hold the team offsite?",
        "description": "We are planning the next team offsite. Pick the place you would enjoy most.",
        "options": ["Mountain cabin", "Beach resort", "City break", "Stay at home and hack"],
    },
    {
        "title": "Which feature should we build next?",
        "description": "Help us decide the roadmap for the next release.",
        "options": ["Dark mode", "Offline support", "Export to PDF", "Keyboard shortcuts"],
    },
]

MESSAGES = {
    "voted": ("Thanks! Your vote has been recorded.", "ok"),
    "already": ("You have already voted in this survey. Here are the current results.", "info"),
    "created": ("Your survey was created. Share it and start collecting votes.", "ok"),
    "invalid": ("Please choose one of the listed options.", "err"),
}

CSS = """
:root { --bg: #FFFFE0; --slate: #2F4F4F; --slate-dark: #213737; --slate-soft: #dbe6e3; --text: #1c1c1c; --muted: #4a5655; }
* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; display: flex; flex-direction: column; background: var(--bg); color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.5; }
.wrap { width: min(860px, 92vw); margin: 0 auto; }
main.wrap { flex: 1; padding: 28px 0 40px; width: min(860px, 92vw); }
.topbar { background: var(--slate); color: var(--bg); }
.bar { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 14px 0; flex-wrap: wrap; }
.brand { color: var(--bg); font-weight: 700; font-size: 1.3rem; text-decoration: none; }
nav a { color: var(--bg); text-decoration: none; margin-left: 10px; padding: 7px 12px; border-radius: 6px; opacity: .9; display: inline-block; }
nav a:hover { background: var(--slate-dark); opacity: 1; }
nav a.active { background: var(--bg); color: var(--slate); opacity: 1; font-weight: 600; }
h1 { color: var(--slate); margin: 0 0 8px; font-size: 2rem; line-height: 1.2; }
h2 { color: var(--slate); font-size: 1.25rem; margin: 0 0 6px; }
h2 a { color: var(--slate); }
.desc, .muted { color: var(--muted); }
.card { border: 2px solid var(--slate); border-radius: 10px; padding: 18px 20px; margin: 14px 0; background: var(--bg); }
.meta { display: flex; gap: 14px; color: var(--muted); font-size: .92rem; margin: 6px 0 12px; flex-wrap: wrap; }
.badge { display: inline-block; background: var(--slate); color: var(--bg); border-radius: 999px; padding: 2px 10px; font-size: .8rem; margin-left: 8px; vertical-align: middle; }
.btn { display: inline-block; background: var(--slate); color: var(--bg); border: 2px solid var(--slate); border-radius: 6px; padding: 9px 18px;
  font: inherit; font-weight: 600; cursor: pointer; text-decoration: none; }
.btn:hover { background: var(--slate-dark); border-color: var(--slate-dark); }
.btn:disabled { opacity: .5; cursor: not-allowed; background: var(--slate); }
.btn.ghost { background: var(--bg); color: var(--slate); }
.btn.ghost:hover { background: var(--slate-soft); }
.actions { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-top: 14px; }
.option { display: flex; align-items: center; gap: 12px; border: 2px solid #b3c0bd; border-radius: 8px; padding: 12px 14px; margin: 10px 0; cursor: pointer; }
.option:hover { border-color: var(--slate); }
.option:has(input:disabled) { opacity: .75; cursor: not-allowed; }
.option:has(input:checked) { border-color: var(--slate); background: var(--slate-soft); }
.option input { accent-color: var(--slate); width: 18px; height: 18px; margin: 0; }
.option span { font-size: 1.05rem; }
.row { margin: 14px 0; }
.rowhead { display: flex; justify-content: space-between; gap: 12px; font-weight: 600; color: var(--slate); }
.track { background: #e6e6c4; border-radius: 999px; height: 16px; overflow: hidden; margin-top: 6px; }
.fill { background: var(--slate); height: 100%; border-radius: 999px; }
.notice { border-left: 6px solid var(--slate); background: var(--slate-soft); padding: 12px 16px; border-radius: 6px; margin: 16px 0; color: var(--slate); }
.notice.err { border-left-color: #8b0000; background: #fbeaea; color: #6b0000; }
.field { display: block; font-weight: 600; color: var(--slate); margin-top: 16px; }
.hint { color: var(--muted); font-size: .9rem; font-weight: normal; }
input[type=text], textarea { display: block; width: 100%; border: 2px solid #b3c0bd; border-radius: 6px; padding: 10px; font: inherit; margin-top: 6px; background: var(--bg); color: var(--text); }
input[type=text]:focus, textarea:focus { outline: none; border-color: var(--slate); }
textarea { min-height: 150px; resize: vertical; }
.empty { text-align: center; padding: 30px; border: 2px dashed var(--slate); border-radius: 10px; color: var(--slate); }
.foot { color: var(--muted); font-size: .9rem; padding: 16px 0 28px; border-top: 1px solid #d6d6b0; }
"""


# ---------------------------------------------------------------- storage

def db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = db()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS polls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER NOT NULL REFERENCES polls(id) ON DELETE CASCADE,
                label TEXT NOT NULL,
                position INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER NOT NULL REFERENCES polls(id) ON DELETE CASCADE,
                option_id INTEGER NOT NULL REFERENCES options(id) ON DELETE CASCADE,
                voter TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE (poll_id, voter)
            );
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM polls").fetchone()[0]
        if count == 0:
            for sample in SAMPLE_POLLS:
                cur = conn.execute(
                    "INSERT INTO polls (title, description) VALUES (?, ?)",
                    (sample["title"], sample["description"]),
                )
                create_options(conn, cur.lastrowid, sample["options"])
        conn.commit()
    finally:
        conn.close()


def create_options(conn, poll_id, labels):
    for position, label in enumerate(labels):
        conn.execute(
            "INSERT INTO options (poll_id, label, position) VALUES (?, ?, ?)",
            (poll_id, label, position),
        )


def get_poll(conn, poll_id):
    return conn.execute("SELECT * FROM polls WHERE id = ?", (poll_id,)).fetchone()


def get_options_with_counts(conn, poll_id):
    return conn.execute(
        """
        SELECT o.id, o.label, COUNT(v.id) AS votes
        FROM options o LEFT JOIN votes v ON v.option_id = o.id
        WHERE o.poll_id = ?
        GROUP BY o.id
        ORDER BY o.position, o.id
        """,
        (poll_id,),
    ).fetchall()


def get_my_vote(conn, poll_id, voter):
    return conn.execute(
        """
        SELECT o.id, o.label FROM votes v JOIN options o ON o.id = v.option_id
        WHERE v.poll_id = ? AND v.voter = ?
        """,
        (poll_id, voter),
    ).fetchone()


# ---------------------------------------------------------------- rendering

def esc(value):
    return html.escape(str(value), quote=True)


def layout(title, body, active=""):
    items = [("/", "Surveys", "surveys"), ("/create", "Create Survey", "create"), ("/results", "Results", "results")]
    links = "".join(
        '<a href="{}"{}>{}</a>'.format(href, ' class="active"' if key == active else "", label)
        for href, label, key in items
    )
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Surveys</title>
<style>{css}</style>
</head>
<body>
<header class="topbar">
  <div class="wrap bar">
    <a class="brand" href="/">Surveys</a>
    <nav aria-label="Main navigation">{links}</nav>
  </div>
</header>
<main class="wrap">
{body}
</main>
<footer class="wrap foot">Cast your vote, then see how everyone else voted.</footer>
</body>
</html>""".format(title=esc(title), css=CSS, links=links, body=body)


def notice_html(msg):
    if msg in MESSAGES:
        text, kind = MESSAGES[msg]
        cls = "notice err" if kind == "err" else "notice"
        return '<div class="{}" role="status">{}</div>'.format(cls, esc(text))
    return ""


def bars_html(options):
    total = sum(o["votes"] for o in options)
    rows = []
    for o in options:
        pct = (o["votes"] * 100.0 / total) if total else 0.0
        rows.append(
            """<div class="row">
  <div class="rowhead"><span>{label}</span><span>{votes} vote{s} ({pct:.1f}%)</span></div>
  <div class="track" role="progressbar" aria-label="{label_attr}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="{pct:.1f}">
    <div class="fill" style="width: {pct:.1f}%"></div>
  </div>
</div>""".format(
                label=esc(o["label"]),
                label_attr=esc(o["label"]),
                votes=o["votes"],
                s="" if o["votes"] == 1 else "s",
                pct=pct,
            )
        )
    return "".join(rows), total


# ---------------------------------------------------------------- handlers

def home(h, q):
    conn = db()
    try:
        polls = conn.execute(
            """
            SELECT p.id, p.title, p.description,
              (SELECT COUNT(*) FROM options WHERE poll_id = p.id) AS option_count,
              (SELECT COUNT(*) FROM votes WHERE poll_id = p.id) AS vote_count,
              (SELECT COUNT(*) FROM votes WHERE poll_id = p.id AND voter = ?) AS mine
            FROM polls p ORDER BY p.id DESC
            """,
            (h.voter,),
        ).fetchall()
    finally:
        conn.close()

    if polls:
        cards = []
        for p in polls:
            badge = '<span class="badge">You voted</span>' if p["mine"] else ""
            action_label = "View survey" if p["mine"] else "Vote"
            cards.append(
                """<article class="card">
  <h2><a href="/surveys/{id}">{title}</a>{badge}</h2>
  <p class="desc">{desc}</p>
  <div class="meta"><span>{opts} options</span><span>{votes} vote{s} so far</span></div>
  <div class="actions">
    <a class="btn" href="/surveys/{id}">{action_label}</a>
    <a class="btn ghost" href="/surveys/{id}/results">View results</a>
  </div>
</article>""".format(
                    id=p["id"],
                    title=esc(p["title"]),
                    desc=esc(p["description"]),
                    badge=badge,
                    action_label=action_label,
                    opts=p["option_count"],
                    votes=p["vote_count"],
                    s="" if p["vote_count"] == 1 else "s",
                )
            )
        listing = "".join(cards)
    else:
        listing = '<div class="empty">No surveys yet. <a href="/create">Create the first one</a>.</div>'

    body = """<h1>Surveys</h1>
<p class="desc">Browse the open surveys below, cast your vote for one option, and see the live results.</p>
{notice}
{listing}""".format(notice=notice_html(first(q, "msg")), listing=listing)
    h.send_html(200, layout("Surveys", body, "surveys"))


def poll_page(h, q, pid):
    conn = db()
    try:
        poll = get_poll(conn, int(pid))
        if poll is None:
            return h.not_found()
        options = get_options_with_counts(conn, poll["id"])
        mine = get_my_vote(conn, poll["id"], h.voter)
    finally:
        conn.close()

    if mine:
        # This browser has already voted in this survey: keep the controls visible
        # but disabled, with the user's choice checked, and show the message.
        msg = ('<div class="notice" role="status">You have already voted in this survey. '
               'Your vote: <strong>{}</strong>.</div>').format(esc(mine["label"]))
        disabled = " disabled"
    else:
        msg = notice_html(first(q, "msg"))
        disabled = ""
    radios = "".join(
        """<label class="option"><input type="radio" name="option" value="{id}" required{attr}><span>{label}</span></label>""".format(
            id=o["id"],
            label=esc(o["label"]),
            attr=disabled + (" checked" if mine and o["id"] == mine["id"] else ""),
        )
        for o in options
    )
    form_html = """<form class="card" method="post" action="/surveys/{pid}/vote">
  <h2>{heading}</h2>
  {radios}
  <div class="actions">
    <button class="btn" type="submit"{disabled}>Submit vote</button>
    <a class="btn ghost" href="/surveys/{pid}/results">View results</a>
  </div>
</form>""".format(
        pid=poll["id"],
        heading="Your vote" if mine else "Choose one option",
        radios=radios,
        disabled=disabled,
    )

    body = """<p><a href="/">&larr; All surveys</a></p>
<h1>{title}</h1>
<p class="desc">{desc}</p>
{msg}
{form}""".format(
        title=esc(poll["title"]),
        desc=esc(poll["description"]),
        msg=msg,
        form=form_html,
    )
    h.send_html(200, layout(poll["title"], body, "surveys"))


def poll_results(h, q, pid):
    conn = db()
    try:
        poll = get_poll(conn, int(pid))
        if poll is None:
            return h.not_found()
        options = get_options_with_counts(conn, poll["id"])
        mine = get_my_vote(conn, poll["id"], h.voter)
    finally:
        conn.close()

    bars, total = bars_html(options)
    vote_link = (
        '<p class="muted">You voted for <strong>{}</strong>.</p>'.format(esc(mine["label"]))
        if mine
        else '<a class="btn" href="/surveys/{}">Cast your vote</a>'.format(poll["id"])
    )
    body = """<p><a href="/results">&larr; All results</a></p>
<h1>{title}</h1>
<p class="desc">{desc}</p>
{msg}
<div class="card">
  <div class="meta"><span><strong>{total}</strong> total vote{s}</span></div>
  {bars}
  <div class="actions">{vote_link}</div>
</div>""".format(
        title=esc(poll["title"]),
        desc=esc(poll["description"]),
        msg=notice_html(first(q, "msg")),
        total=total,
        s="" if total == 1 else "s",
        bars=bars or '<p class="muted">No options yet.</p>',
        vote_link=vote_link,
    )
    h.send_html(200, layout(poll["title"] + " results", body, "results"))


def results_overview(h, q):
    conn = db()
    try:
        polls = conn.execute("SELECT id, title, description FROM polls ORDER BY id DESC").fetchall()
        sections = []
        for p in polls:
            options = get_options_with_counts(conn, p["id"])
            bars, total = bars_html(options)
            sections.append(
                """<section class="card">
  <h2><a href="/surveys/{id}/results">{title}</a></h2>
  <div class="meta"><span><strong>{total}</strong> total vote{s}</span></div>
  {bars}
</section>""".format(
                    id=p["id"],
                    title=esc(p["title"]),
                    total=total,
                    s="" if total == 1 else "s",
                    bars=bars,
                )
            )
    finally:
        conn.close()

    listing = "".join(sections) or '<div class="empty">No surveys yet. <a href="/create">Create one</a>.</div>'
    body = """<h1>Results</h1>
<p class="desc">Live vote counts for every survey. Select a survey title to see its full results page.</p>
{}""".format(listing)
    h.send_html(200, layout("Results", body, "results"))


def cast_vote(h, q, pid):
    form = h.read_form()
    raw = first(form, "option")
    conn = db()
    try:
        poll = get_poll(conn, int(pid))
        if poll is None:
            return h.not_found()
        # One vote per poll per browser: never record a second vote, even if posted directly.
        if get_my_vote(conn, poll["id"], h.voter):
            return h.redirect("/surveys/{}/results?msg=already".format(poll["id"]))
        try:
            option_id = int(raw)
        except ValueError:
            option_id = None
        option = None
        if option_id is not None:
            option = conn.execute(
                "SELECT id FROM options WHERE id = ? AND poll_id = ?", (option_id, poll["id"])
            ).fetchone()
        if option is None:
            return h.redirect("/surveys/{}?msg=invalid".format(poll["id"]))
        try:
            conn.execute(
                "INSERT INTO votes (poll_id, option_id, voter) VALUES (?, ?, ?)",
                (poll["id"], option["id"], h.voter),
            )
            conn.commit()
            msg = "voted"
        except sqlite3.IntegrityError:
            msg = "already"
        return h.redirect("/surveys/{}/results?msg={}".format(poll["id"], msg))
    finally:
        conn.close()


def create_form(h, q, errors=(), title="", desc="", options_text=""):
    error_html = ""
    if errors:
        error_html = '<div class="notice err" role="alert"><ul style="margin:0;padding-left:18px">{}</ul></div>'.format(
            "".join("<li>{}</li>".format(esc(e)) for e in errors)
        )
    body = """<h1>Create a survey</h1>
<p class="desc">Give your survey a question and at least two options. Put one option on each line.</p>
{errors}
<form class="card" method="post" action="/create">
  <label class="field" for="title">Question / title <span class="hint">(required, max {max_title} characters)</span></label>
  <input type="text" id="title" name="title" value="{title}" maxlength="{max_title}" required>

  <label class="field" for="description">Description <span class="hint">(optional)</span></label>
  <textarea id="description" name="description" style="min-height:90px">{desc}</textarea>

  <label class="field" for="options">Options <span class="hint">(one per line, 2 to {max_options})</span></label>
  <textarea id="options" name="options" placeholder="Option A&#10;Option B&#10;Option C">{options}</textarea>

  <div class="actions"><button class="btn" type="submit">Create survey</button><a class="btn ghost" href="/">Cancel</a></div>
</form>""".format(
        errors=error_html,
        title=esc(title),
        desc=esc(desc),
        options=esc(options_text),
        max_title=MAX_TITLE,
        max_options=MAX_OPTIONS,
    )
    h.send_html(200, layout("Create survey", body, "create"))


def create_post(h, q):
    form = h.read_form()
    title = first(form, "title").strip()
    desc = first(form, "description").strip()
    raw_options = first(form, "options")
    labels = []
    for line in raw_options.splitlines():
        line = line.strip()
        if line and line not in labels:
            labels.append(line)

    errors = []
    if not title:
        errors.append("Please enter a question or title.")
    elif len(title) > MAX_TITLE:
        errors.append("The title must be {} characters or fewer.".format(MAX_TITLE))
    if len(labels) < 2:
        errors.append("Please enter at least two different options.")
    elif len(labels) > MAX_OPTIONS:
        errors.append("A survey can have at most {} options.".format(MAX_OPTIONS))
    elif any(len(label) > MAX_OPTION for label in labels):
        errors.append("Each option must be {} characters or fewer.".format(MAX_OPTION))
    if errors:
        return create_form(h, q, errors, title, desc, raw_options)

    conn = db()
    try:
        cur = conn.execute("INSERT INTO polls (title, description) VALUES (?, ?)", (title, desc))
        create_options(conn, cur.lastrowid, labels)
        conn.commit()
        poll_id = cur.lastrowid
    finally:
        conn.close()
    h.redirect("/surveys/{}?msg=created".format(poll_id))


def legacy_redirect(h, q, pid=None, results=None):
    # Old /polls/... links (before the rename to surveys) go to the new address.
    if pid is None:
        return h.redirect("/")
    return h.redirect("/surveys/{}{}".format(pid, results or ""))


def not_found_page(h, q):
    h.not_found()


def first(params, key):
    values = params.get(key) or [""]
    return values[0] or ""


# ---------------------------------------------------------------- routing

ROUTES = [
    ("GET", re.compile(r"^/$"), home),
    ("GET", re.compile(r"^/results$"), results_overview),
    ("GET", re.compile(r"^/create$"), create_form),
    ("POST", re.compile(r"^/create$"), create_post),
    ("GET", re.compile(r"^/surveys/(\d+)$"), poll_page),
    ("POST", re.compile(r"^/surveys/(\d+)/vote$"), cast_vote),
    ("GET", re.compile(r"^/surveys/(\d+)/results$"), poll_results),
    ("GET", re.compile(r"^/polls(?:/(\d+)(/results)?)?$"), legacy_redirect),
]


class Handler(BaseHTTPRequestHandler):
    server_version = "SurveysSite/1.0"

    def log_message(self, fmt, *args):  # keep the console quiet
        pass

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    def dispatch(self, method):
        cookies = SimpleCookie(self.headers.get("Cookie", ""))
        if "voter" in cookies and cookies["voter"].value:
            self.voter = cookies["voter"].value
            self.new_voter = False
        else:
            self.voter = uuid.uuid4().hex
            self.new_voter = True

        url = urllib.parse.urlsplit(self.path)
        path = url.path.rstrip("/") or "/"
        query = urllib.parse.parse_qs(url.query, keep_blank_values=True)

        path_matched = False
        try:
            for route_method, pattern, handler in ROUTES:
                match = pattern.match(path)
                if not match:
                    continue
                path_matched = True
                if route_method != method:
                    continue
                return handler(self, query, *match.groups())
            if path_matched:
                return self.send_html(405, layout("Method not allowed", "<h1>Method not allowed</h1>"))
            return self.not_found()
        except Exception as exc:  # pragma: no cover - last-resort safety net
            return self.send_html(
                500,
                layout("Error", "<h1>Something went wrong</h1><p class=\"desc\">{}</p>".format(esc(exc))),
            )

    def read_form(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode("utf-8", "replace") if length else ""
        return urllib.parse.parse_qs(body, keep_blank_values=True)

    def send_raw(self, status, data, content_type, headers=()):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        if self.new_voter:
            self.send_header(
                "Set-Cookie", "voter={}; Path=/; Max-Age=31536000; HttpOnly; SameSite=Lax".format(self.voter)
            )
            self.new_voter = False
        for key, value in headers:
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def send_html(self, status, document):
        self.send_raw(status, document.encode("utf-8"), "text/html; charset=utf-8")

    def redirect(self, location):
        self.send_raw(303, b"", "text/plain; charset=utf-8", headers=[("Location", location)])

    def not_found(self):
        self.send_html(
            404,
            layout("Not found", '<h1>Page not found</h1><p class="desc">That page does not exist.</p>'
                   '<p><a class="btn" href="/">Back to surveys</a></p>'),
        )


class Server(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    init_db()
    httpd = Server(("127.0.0.1", PORT), Handler)
    print("Surveys site running at http://127.0.0.1:{} (data: {})".format(PORT, DB_PATH), flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
