#!/usr/bin/env python3
"""Wheel of Fortune web server.

Standard library only (http.server + sqlite3). Configuration via environment:
  PORT      port to listen on (default 8000), bound to 127.0.0.1
  DATA_DIR  directory for the SQLite database (default ./data)
"""
import json
import mimetypes
import os
import random
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATA_DIR = os.path.abspath(os.environ.get("DATA_DIR") or os.path.join(BASE_DIR, "data"))
PORT = int(os.environ.get("PORT") or 8000)
DB_PATH = os.path.join(DATA_DIR, "wheel.db")

MAX_NAME_LENGTH = 40

# Sample prizes used when the database is empty.
# (name, description, weight = relative chance, is_win)
SAMPLE_PRIZES = [
    ("$50 Gift Card", "Redeem at any partner store.", 1, 1),
    ("Free Coffee", "One regular coffee on us.", 6, 1),
    ("10% Discount", "Applies to your next order.", 8, 1),
    ("Mystery Gift", "A surprise waiting at the counter.", 3, 1),
    ("Free Dessert", "Choose any dessert from the menu.", 5, 1),
    ("Try Again", "No prize this time. Spin again!", 15, 0),
    ("Bonus Points x2", "Double your loyalty points today.", 10, 1),
    ("Extra Spin", "One more free spin on the house.", 7, 1),
]

# Sample winners seeded into an empty spin history so the records pages have content.
SAMPLE_SPINS = [
    ("Alice", "Free Coffee", 1, 5),
    ("Bob", "Bonus Points x2", 1, 3),
    ("Chen", "Try Again", 0, 2),
    ("Alice", "10% Discount", 1, 1),
]


@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    with db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS prizes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                weight REAL NOT NULL,
                is_win INTEGER NOT NULL DEFAULT 1,
                position INTEGER NOT NULL DEFAULT 0)"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS spins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player TEXT NOT NULL,
                prize_id INTEGER NOT NULL,
                prize_name TEXT NOT NULL,
                is_win INTEGER NOT NULL,
                created_at TEXT NOT NULL)"""
        )
        if conn.execute("SELECT COUNT(*) FROM prizes").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO prizes (name, description, weight, is_win, position) VALUES (?, ?, ?, ?, ?)",
                [(n, d, w, iw, i) for i, (n, d, w, iw) in enumerate(SAMPLE_PRIZES)],
            )
        if conn.execute("SELECT COUNT(*) FROM spins").fetchone()[0] == 0:
            prize_ids = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM prizes")}
            now = datetime.now(timezone.utc)
            for player, prize_name, is_win, hours_ago in SAMPLE_SPINS:
                conn.execute(
                    "INSERT INTO spins (player, prize_id, prize_name, is_win, created_at) VALUES (?, ?, ?, ?, ?)",
                    (
                        player,
                        prize_ids[prize_name],
                        prize_name,
                        is_win,
                        (now - timedelta(hours=hours_ago)).isoformat(timespec="seconds"),
                    ),
                )


def list_prizes():
    with db() as conn:
        rows = conn.execute(
            "SELECT id, name, description, weight, is_win FROM prizes ORDER BY position, id"
        ).fetchall()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "description": r["description"],
            "weight": r["weight"],
            "is_win": bool(r["is_win"]),
        }
        for r in rows
    ]


def spin(player):
    with db() as conn:
        rows = conn.execute(
            "SELECT id, name, weight, is_win FROM prizes WHERE weight > 0 ORDER BY position, id"
        ).fetchall()
        if not rows:
            raise RuntimeError("No prizes are configured.")
        chosen = random.choices(rows, weights=[r["weight"] for r in rows], k=1)[0]
        created = now_iso()
        cur = conn.execute(
            "INSERT INTO spins (player, prize_id, prize_name, is_win, created_at) VALUES (?, ?, ?, ?, ?)",
            (player, chosen["id"], chosen["name"], chosen["is_win"], created),
        )
        spin_id = cur.lastrowid
    return {
        "spin": {
            "id": spin_id,
            "player": player,
            "created_at": created,
        },
        "prize": {
            "id": chosen["id"],
            "name": chosen["name"],
            "is_win": bool(chosen["is_win"]),
        },
    }


def _spin_rows(rows):
    return [
        {
            "id": r["id"],
            "player": r["player"],
            "prize_id": r["prize_id"],
            "prize_name": r["prize_name"],
            "is_win": bool(r["is_win"]),
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def list_spins_for(player):
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM spins WHERE player = ? COLLATE NOCASE ORDER BY id DESC LIMIT 500",
            (player,),
        ).fetchall()
    return _spin_rows(rows)


def list_recent_winners(limit=10):
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM spins WHERE is_win = 1 ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return _spin_rows(rows)


PAGES = {
    "/": "index.html",
    "/prizes": "prizes.html",
    "/records": "records.html",
}


class Handler(BaseHTTPRequestHandler):
    server_version = "WheelOfFortune/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_static(self, rel_path):
        full = os.path.normpath(os.path.join(STATIC_DIR, rel_path))
        if not full.startswith(STATIC_DIR + os.sep) or not os.path.isfile(full):
            self.send_error(404, "Not found")
            return
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        with open(full, "rb") as fh:
            body = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        try:
            url = urlparse(self.path)
            path = url.path
            if path == "/api/prizes":
                return self.send_json(200, {"prizes": list_prizes()})
            if path == "/api/spins":
                player = parse_qs(url.query).get("player", [""])[0].strip()[:MAX_NAME_LENGTH]
                if not player:
                    return self.send_json(400, {"error": "Enter a player name to see your records."})
                return self.send_json(200, {"player": player, "spins": list_spins_for(player)})
            if path == "/api/winners":
                return self.send_json(200, {"winners": list_recent_winners()})
            if path in PAGES:
                return self.send_static(PAGES[path])
            if path.startswith("/static/"):
                return self.send_static(path[len("/static/"):])
            self.send_error(404, "Not found")
        except Exception as exc:  # keep the server alive, report the failure
            self.send_json(500, {"error": str(exc)})

    def do_POST(self):
        try:
            if urlparse(self.path).path != "/api/spin":
                return self.send_error(404, "Not found")
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            try:
                data = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                return self.send_json(400, {"error": "Invalid request body."})
            player = str(data.get("player", "")).strip()[:MAX_NAME_LENGTH]
            if not player:
                return self.send_json(400, {"error": "Please enter your name before spinning."})
            return self.send_json(200, spin(player))
        except Exception as exc:
            self.send_json(500, {"error": str(exc)})


def main():
    init_db()
    ThreadingHTTPServer.daemon_threads = True
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Wheel of Fortune running at http://127.0.0.1:{PORT} (data: {DATA_DIR})", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
