"""Polls website: server-rendered HTML pages backed by SQLite (standard library only)."""
import html
import http.cookies
import os
import sqlite3
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "polls.db")

SAMPLE_POLLS = [
    {
        "question": "What is your favorite programming language?",
        "description": "Pick the language you enjoy writing the most.",
        "options": ["Python", "JavaScript", "Go", "Rust", "Java"],
    },
    {
        "question": "Where should the team hold the year-end party?",
        "description": "The venue will be booked as soon as the majority is clear.",
        "options": ["Rooftop restaurant", "Bowling alley", "Hot spring inn", "Office lounge"],
    },
    {
        "question": "Which weekend activity do you prefer?",
        "description": "Choose the one you would most like to do this season.",
        "options": ["Hiking", "Board games", "Cooking together", "Movie marathon", "Beach day"],
    },
    {
        "question": "Which office plant should we add next?",
        "description": "Only one plant can be added, so vote for your favorite.",
        "options": ["Monstera", "Snake plant", "Pothos", "Fiddle leaf fig"],
    },
]


CREATE_OPTION_SLOTS = 6
MAX_QUESTION_LEN = 200
MAX_OPTION_LEN = 100


def db_connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = db_connect()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS polls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
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
                created_at TEXT NOT NULL
            );
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM polls").fetchone()[0]
        if count == 0:
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            for poll in SAMPLE_POLLS:
                cur = conn.execute(
                    "INSERT INTO polls (question, description, created_at) VALUES (?, ?, ?)",
                    (poll["question"], poll["description"], now),
                )
                for pos, text in enumerate(poll["options"]):
                    conn.execute(
                        "INSERT INTO options (poll_id, text, position) VALUES (?, ?, ?)",
                        (cur.lastrowid, text, pos),
                    )
            # Give the sample polls some votes so the results pages are not empty.
            seed_votes = {1: [0, 0, 1, 2, 0, 1], 2: [0, 1, 1, 2, 0], 3: [0, 3, 2, 1, 0, 4], 4: [1, 1, 0, 2]}
            for poll_id, picks in seed_votes.items():
                opts = conn.execute(
                    "SELECT id FROM options WHERE poll_id = ? ORDER BY position", (poll_id,)
                ).fetchall()
                for pick in picks:
                    if pick < len(opts):
                        conn.execute(
                            "INSERT INTO votes (poll_id, option_id, created_at) VALUES (?, ?, ?)",
                            (poll_id, opts[pick]["id"], now),
                        )
            conn.commit()
    finally:
        conn.close()


def get_poll(conn, poll_id):
    return conn.execute("SELECT * FROM polls WHERE id = ?", (poll_id,)).fetchone()


def get_results(conn, poll_id):
    """Return options with vote counts and percentages for one poll."""
    rows = conn.execute(
        """
        SELECT o.id, o.text, COUNT(v.id) AS votes
        FROM options o LEFT JOIN votes v ON v.option_id = o.id
        WHERE o.poll_id = ?
        GROUP BY o.id ORDER BY o.position
        """,
        (poll_id,),
    ).fetchall()
    total = sum(r["votes"] for r in rows)
    results = []
    for r in rows:
        pct = round(r["votes"] * 100.0 / total, 1) if total else 0.0
        results.append({"id": r["id"], "text": r["text"], "votes": r["votes"], "pct": pct})
    return results, total


def layout(title, body, active=""):
    def link(href, label, key):
        cls = ' class="active"' if key == active else ""
        return f'<a href="{href}"{cls}>{label}</a>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} | Polls</title>
<style>
  :root {{ --slate: #2F4F4F; --slate-dark: #1E3333; --slate-light: #F3F0C0; --cream: #FFFFE0; --paper: #FFFFF2; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: var(--cream); color: var(--slate); line-height: 1.5; }}
  header {{ background: var(--slate); color: var(--cream); }}
  header .bar {{ max-width: 960px; margin: 0 auto; padding: 14px 20px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; }}
  header .brand {{ font-size: 1.3rem; font-weight: bold; color: var(--cream); text-decoration: none; }}
  nav a {{ color: var(--cream); text-decoration: none; margin-left: 18px; padding: 6px 4px; border-bottom: 2px solid transparent; }}
  nav a:hover, nav a.active {{ border-bottom-color: var(--cream); }}
  main {{ max-width: 960px; margin: 0 auto; padding: 28px 20px 60px; }}
  h1 {{ color: var(--slate); margin: 0 0 8px; font-size: 1.9rem; }}
  h2 {{ color: var(--slate); font-size: 1.3rem; }}
  .lead {{ color: var(--slate); opacity: 0.9; margin-top: 0; }}
  .breadcrumb {{ font-size: 0.9rem; margin-bottom: 14px; }}
  .breadcrumb a {{ color: var(--slate); }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 18px; margin-top: 20px; }}
  .card {{ border: 2px solid var(--slate); border-radius: 8px; padding: 18px; display: flex; flex-direction: column; background: var(--paper); box-shadow: 3px 3px 0 var(--slate); }}
  .card h3 {{ margin: 0 0 8px; color: var(--slate); font-size: 1.1rem; }}
  .card p {{ margin: 0 0 14px; flex: 1; color: var(--slate); }}
  .meta {{ font-size: 0.9rem; color: var(--slate); opacity: 0.85; margin-bottom: 10px; }}
  .btn {{ display: inline-block; background: var(--slate); color: var(--cream); border: 2px solid var(--slate); padding: 9px 18px; border-radius: 6px; text-decoration: none; font-size: 1rem; cursor: pointer; font-family: inherit; }}
  .btn:hover {{ background: var(--slate-dark); border-color: var(--slate-dark); }}
  .btn:disabled, .btn[disabled] {{ background: #B9C4C0; border-color: #B9C4C0; color: #4A5E5C; cursor: not-allowed; }}
  .btn.outline {{ background: var(--paper); color: var(--slate); }}
  .btn.outline:hover {{ background: var(--slate-light); }}
  .panel {{ border: 2px solid var(--slate); border-radius: 8px; padding: 22px; margin-top: 18px; background: var(--paper); }}
  .option {{ display: flex; align-items: center; gap: 10px; padding: 12px 14px; border: 2px solid var(--slate); border-radius: 6px; margin-bottom: 10px; cursor: pointer; background: var(--paper); }}
  .option:hover {{ background: var(--slate-light); }}
  .option.disabled {{ cursor: not-allowed; opacity: 0.6; }}
  .option.disabled:hover {{ background: var(--paper); }}
  .option input {{ width: 18px; height: 18px; accent-color: var(--slate); margin: 0; }}
  .option span {{ font-size: 1.05rem; }}
  .notice {{ border: 2px solid var(--slate); background: var(--slate-light); border-radius: 6px; padding: 12px 16px; margin: 16px 0; color: var(--slate); }}
  .notice.error {{ background: var(--paper); border-style: dashed; }}
  .result-row {{ margin: 18px 0; }}
  .result-head {{ display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 6px; }}
  .bar-track {{ background: var(--slate-light); border: 2px solid var(--slate); border-radius: 6px; height: 26px; overflow: hidden; }}
  .bar-fill {{ background: #7A9A96; height: 100%; min-width: 0; }}
  .bar-fill.winner {{ background: var(--slate); }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
  th, td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--slate); color: var(--slate); }}
  th {{ background: var(--slate-light); }}
  .actions {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 18px; }}
  .empty {{ border: 2px dashed var(--slate); border-radius: 8px; padding: 24px; text-align: center; color: var(--slate); background: var(--paper); }}
  footer {{ text-align: center; color: var(--slate); font-size: 0.9rem; padding: 20px; border-top: 2px solid var(--slate); }}
  .field {{ display: block; margin-bottom: 16px; }}
  .field > span {{ display: block; font-weight: bold; margin-bottom: 4px; color: var(--slate); }}
  .field input {{ width: 100%; padding: 9px 10px; border: 2px solid var(--slate); border-radius: 6px; font: inherit; background: var(--paper); color: var(--slate); }}
  .field input:focus {{ outline: 3px solid var(--slate-light); }}
  .hint {{ font-size: 0.9rem; opacity: 0.85; margin: 0 0 12px; }}
  @media (max-width: 600px) {{ nav a {{ margin-left: 10px; }} h1 {{ font-size: 1.5rem; }} }}
</style>
</head>
<body>
<header>
  <div class="bar">
    <a class="brand" href="/">Polls</a>
    <nav>
      {link("/", "Home", "home")}
      {link("/polls", "All Polls", "polls")}
      {link("/results", "Results", "results")}
      {link("/polls/new", "Create poll", "create")}
    </nav>
  </div>
</header>
<main>
{body}
</main>
<footer>Polls &mdash; cast your vote and see what everyone thinks.</footer>
</body>
</html>
"""


def page_home(conn, query):
    polls = conn.execute(
        """
        SELECT p.id, p.question, p.description,
               (SELECT COUNT(*) FROM votes v WHERE v.poll_id = p.id) AS total,
               (SELECT COUNT(*) FROM options o WHERE o.poll_id = p.id) AS option_count
        FROM polls p ORDER BY p.id
        """
    ).fetchall()
    cards = "".join(
        f"""<div class="card">
          <h3>{html.escape(p['question'])}</h3>
          <p>{html.escape(p['description'])}</p>
          <div class="meta">{p['option_count']} options &middot; {p['total']} vote{'' if p['total'] == 1 else 's'} so far</div>
          <div class="actions" style="margin-top:0">
            <a class="btn" href="/polls/{p['id']}">Vote</a>
            <a class="btn outline" href="/polls/{p['id']}/results">Results</a>
          </div>
        </div>"""
        for p in polls
    )
    body = f"""<h1>Welcome to Polls</h1>
<p class="lead">Browse the open polls below, cast your vote for one option, and then look at the live results.</p>
<div class="actions">
  <a class="btn" href="/polls">Browse all polls</a>
  <a class="btn outline" href="/results">View all results</a>
  <a class="btn outline" href="/polls/new">Create a poll</a>
</div>
<h2 style="margin-top:32px">Featured polls</h2>
<div class="cards">{cards or '<div class="empty">There are no polls yet.</div>'}</div>"""
    return layout("Home", body, "home")


def page_polls(conn, query):
    polls = conn.execute(
        """
        SELECT p.id, p.question, p.description,
               (SELECT COUNT(*) FROM votes v WHERE v.poll_id = p.id) AS total
        FROM polls p ORDER BY p.id
        """
    ).fetchall()
    rows = "".join(
        f"""<tr>
          <td><a href="/polls/{p['id']}"><strong>{html.escape(p['question'])}</strong></a><br>
          <span>{html.escape(p['description'])}</span></td>
          <td>{p['total']}</td>
          <td><a class="btn" href="/polls/{p['id']}">Vote</a>
          <a class="btn outline" href="/polls/{p['id']}/results">Results</a></td>
        </tr>"""
        for p in polls
    )
    body = f"""<h1>All Polls</h1>
<p class="lead">Choose a poll to vote, or open its results. <a href="/polls/new">Create a new poll</a>.</p>
<div class="panel">
<table>
  <thead><tr><th>Poll</th><th>Votes</th><th>Actions</th></tr></thead>
  <tbody>{rows or '<tr><td colspan="3">There are no polls yet.</td></tr>'}</tbody>
</table>
</div>"""
    return layout("All Polls", body, "polls")


def page_poll(conn, poll_id, query, cookies):
    poll = get_poll(conn, poll_id)
    if poll is None:
        return page_not_found()
    options = conn.execute(
        "SELECT id, text FROM options WHERE poll_id = ? ORDER BY position", (poll_id,)
    ).fetchall()
    notice = ""
    if "error" in query:
        notice = '<div class="notice error">Please select one option before submitting your vote.</div>'
    if "created" in query:
        notice = '<div class="notice">Your poll has been created. Cast your vote below, and the results will show the counts.</div>'
    if "voted" in cookies:
        notice += '<div class="notice">You have already voted in this poll from this browser. You can still look at the results.</div>'
    voted = "voted" in cookies
    if voted:
        notice = '<div class="notice">You have already voted in this poll. Your voting controls are disabled; you can still look at the results.</div>'
    disabled = " disabled" if voted else ""
    radios = "".join(
        f"""<label class="option{' disabled' if voted else ''}"><input type="radio" name="option_id" value="{o['id']}" required{disabled}>
        <span>{html.escape(o['text'])}</span></label>"""
        for o in options
    )
    form = f"""<form method="post" action="/polls/{poll_id}/vote">
      {radios}
      <div class="actions">
        <button class="btn" type="submit"{disabled}>Submit my vote</button>
        <a class="btn outline" href="/polls/{poll_id}/results">View results</a>
      </div>
    </form>"""
    body = f"""<div class="breadcrumb"><a href="/">Home</a> &rsaquo; <a href="/polls">All Polls</a> &rsaquo; Poll {poll_id}</div>
<h1>{html.escape(poll['question'])}</h1>
<p class="lead">{html.escape(poll['description'])}</p>
{notice}
<div class="panel">
  <h2 style="margin-top:0">Choose one option</h2>
  {form}
</div>"""
    return layout(poll["question"], body, "polls")


def page_results_one(conn, poll_id, query):
    poll = get_poll(conn, poll_id)
    if poll is None:
        return page_not_found()
    results, total = get_results(conn, poll_id)
    top = max((r["votes"] for r in results), default=0)
    rows = ""
    for r in results:
        winner = " winner" if total and r["votes"] == top else ""
        rows += f"""<div class="result-row">
          <div class="result-head"><span>{html.escape(r['text'])}</span><span>{r['votes']} vote{'' if r['votes'] == 1 else 's'} ({r['pct']}%)</span></div>
          <div class="bar-track"><div class="bar-fill{winner}" style="width:{r['pct']}%"></div></div>
        </div>"""
    if not total:
        rows = '<div class="notice">Nobody has voted in this poll yet. Every option starts at zero.</div>' + rows
    body = f"""<div class="breadcrumb"><a href="/">Home</a> &rsaquo; <a href="/results">Results</a> &rsaquo; Poll {poll_id}</div>
<h1>Results: {html.escape(poll['question'])}</h1>
<p class="lead">Total votes: <strong>{total}</strong>. The darkest bar is the leading option.</p>
<div class="panel">{rows}
  <div class="actions">
    <a class="btn" href="/polls/{poll_id}">Vote in this poll</a>
    <a class="btn outline" href="/results">All results</a>
  </div>
</div>"""
    return layout("Results", body, "results")


def page_results_all(conn, query):
    polls = conn.execute(
        """
        SELECT p.id, p.question,
               (SELECT COUNT(*) FROM votes v WHERE v.poll_id = p.id) AS total
        FROM polls p ORDER BY p.id
        """
    ).fetchall()
    rows = "".join(
        f"""<tr><td><a href="/polls/{p['id']}/results"><strong>{html.escape(p['question'])}</strong></a></td>
        <td>{p['total']}</td>
        <td><a class="btn outline" href="/polls/{p['id']}/results">Open results</a></td></tr>"""
        for p in polls
    )
    body = f"""<h1>Results</h1>
<p class="lead">Pick a poll to see how the votes are distributed.</p>
<div class="panel">
<table>
  <thead><tr><th>Poll</th><th>Total votes</th><th></th></tr></thead>
  <tbody>{rows or '<tr><td colspan="3">There are no polls yet.</td></tr>'}</tbody>
</table>
</div>"""
    return layout("Results", body, "results")


def page_create_poll(values, error=""):
    question = values["question"]
    options = values["options"]
    err = f'<div class="notice error" role="alert">{html.escape(error)}</div>' if error else ""
    fields = "".join(
        f"""<label class="field"><span>Option {i + 1}{' (required)' if i < 2 else ' (optional)'}</span>
        <input type="text" name="option_{i + 1}" value="{html.escape(opt, quote=True)}" maxlength="{MAX_OPTION_LEN}"{' required' if i < 2 else ''}></label>"""
        for i, opt in enumerate(options)
    )
    body = f"""<div class="breadcrumb"><a href="/">Home</a> &rsaquo; Create poll</div>
<h1>Create a poll</h1>
<p class="lead">Enter a question and at least two options. The new poll appears on the voting page right away.</p>
{err}
<div class="panel">
  <form method="post" action="/polls">
    <label class="field"><span>Question (required)</span>
      <input type="text" name="question" value="{html.escape(question, quote=True)}" maxlength="{MAX_QUESTION_LEN}" required></label>
    <h2 style="margin-top:0">Options</h2>
    <p class="hint">Fill in at least two options. Leave the optional fields empty if you do not need them.</p>
    {fields}
    <div class="actions">
      <button class="btn" type="submit">Create poll</button>
      <a class="btn outline" href="/polls">Cancel</a>
    </div>
  </form>
</div>"""
    return layout("Create poll", body, "create")


def create_poll(conn, form):
    """Validate the submitted form and insert the poll. Returns (poll_id, None) or (None, (values, error))."""
    question = form.get("question", [""])[0].strip()
    options = [form.get(f"option_{i}", [""])[0].strip() for i in range(1, CREATE_OPTION_SLOTS + 1)]
    values = {"question": question, "options": options}
    filled = [o for o in options if o]
    error = ""
    if not question:
        error = "Please enter a question for your poll."
    elif len(question) > MAX_QUESTION_LEN:
        error = f"The question must be {MAX_QUESTION_LEN} characters or fewer."
    elif len(filled) < 2:
        error = "Please enter at least two options."
    elif any(len(o) > MAX_OPTION_LEN for o in filled):
        error = f"Each option must be {MAX_OPTION_LEN} characters or fewer."
    if error:
        return None, (values, error)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cur = conn.execute(
        "INSERT INTO polls (question, description, created_at) VALUES (?, ?, ?)",
        (question, "", now),
    )
    poll_id = cur.lastrowid
    for pos, text in enumerate(filled):
        conn.execute(
            "INSERT INTO options (poll_id, text, position) VALUES (?, ?, ?)",
            (poll_id, text, pos),
        )
    conn.commit()
    return poll_id, None


def page_not_found():
    body = """<h1>Page not found</h1>
<p class="lead">The page you asked for does not exist.</p>
<div class="actions"><a class="btn" href="/">Go to Home</a> <a class="btn outline" href="/polls">All Polls</a></div>"""
    return layout("Not found", body)


class Handler(BaseHTTPRequestHandler):
    server_version = "PollsSite/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, status, body, headers=None):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        for k, v in (headers or []):
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, location, headers=None):
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        for k, v in (headers or []):
            self.send_header(k, v)
        self.end_headers()

    def _cookies(self):
        jar = http.cookies.SimpleCookie(self.headers.get("Cookie", ""))
        return {k: m.value for k, m in jar.items()}

    def _route_get(self, path, query):
        conn = db_connect()
        try:
            if path == "/":
                return 200, page_home(conn, query), []
            if path == "/polls":
                return 200, page_polls(conn, query), []
            if path == "/results":
                return 200, page_results_all(conn, query), []
            if path == "/polls/new":
                return 200, page_create_poll({"question": "", "options": [""] * CREATE_OPTION_SLOTS}), []
            parts = [p for p in path.split("/") if p]
            if len(parts) >= 2 and parts[0] == "polls" and parts[1].isdigit():
                poll_id = int(parts[1])
                if len(parts) == 2:
                    cookies = self._cookies()
                    voted = f"voted_{poll_id}" in cookies
                    cookies_view = {"voted"} if voted else set()
                    status = 200 if get_poll(conn, poll_id) else 404
                    return status, page_poll(conn, poll_id, query, cookies_view), []
                if len(parts) == 3 and parts[2] == "results":
                    status = 200 if get_poll(conn, poll_id) else 404
                    return status, page_results_one(conn, poll_id, query), []
            return 404, page_not_found(), []
        finally:
            conn.close()

    def do_GET(self):
        url = urlsplit(self.path)
        query = parse_qs(url.query)
        status, body, headers = self._route_get(url.path, query)
        self._send(status, body, headers)

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        url = urlsplit(self.path)
        parts = [p for p in url.path.split("/") if p]
        length = int(self.headers.get("Content-Length") or 0)
        form = parse_qs(self.rfile.read(length).decode("utf-8", "replace"))
        if parts == ["polls"]:
            conn = db_connect()
            try:
                poll_id, failure = create_poll(conn, form)
            finally:
                conn.close()
            if failure:
                values, error = failure
                return self._send(400, page_create_poll(values, error))
            return self._redirect(f"/polls/{poll_id}?created=1")
        if len(parts) == 3 and parts[0] == "polls" and parts[1].isdigit() and parts[2] == "vote":
            poll_id = int(parts[1])
            conn = db_connect()
            try:
                if get_poll(conn, poll_id) is None:
                    return self._send(404, page_not_found())
                cookies = self._cookies()
                if f"voted_{poll_id}" in cookies:
                    return self._redirect(f"/polls/{poll_id}")
                raw = form.get("option_id", [""])[0]
                option = None
                if raw.isdigit():
                    option = conn.execute(
                        "SELECT id FROM options WHERE id = ? AND poll_id = ?", (int(raw), poll_id)
                    ).fetchone()
                if option is None:
                    return self._redirect(f"/polls/{poll_id}?error=1")
                now = datetime.now(timezone.utc).isoformat(timespec="seconds")
                conn.execute(
                    "INSERT INTO votes (poll_id, option_id, created_at) VALUES (?, ?, ?)",
                    (poll_id, option["id"], now),
                )
                conn.commit()
            finally:
                conn.close()
            return self._redirect(
                f"/polls/{poll_id}/results",
                headers=[("Set-Cookie", f"voted_{poll_id}=1; Path=/; Max-Age=31536000; SameSite=Lax")],
            )
        self._send(404, page_not_found())


def main():
    port = int(os.environ.get("PORT") or 8000)
    init_db()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Polls site running at http://127.0.0.1:{port} (data: {DATA_DIR})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
