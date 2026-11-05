#!/usr/bin/env python3
"""Wheel of Fortune web server.

Uses only the Python standard library (http.server + sqlite3).
Environment variables:
  PORT      port to listen on (default 8000)
  DATA_DIR  directory for the SQLite database (default: ./data)
"""
import json
import os
import random
import re
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "wheel.db")
PORT = int(os.environ.get("PORT") or 8000)

PAGES = {
    "/": "index.html",
    "/prizes": "prizes.html",
    "/my-records": "records.html",
}

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
}

# Sample prizes, used only when the database has no prizes yet.
# (name, description, weight, segment colour, ...)
SAMPLE_PRIZES = [
    ("$50 Gift Card", "Redeemable at major online stores.", 2, "#8b0000"),
    ("Free Coffee", "One regular coffee at any partner cafe.", 8, "#d9d9d9"),
    ("10% Off Coupon", "Ten percent off your next order.", 12, "#a61c1c"),
    ("Bonus Spin", "Take one more turn on the wheel.", 10, "#bfbfbf"),
    ("Mystery Gift", "A surprise package is on its way.", 4, "#6e0b0b"),
    ("Free Shipping", "Free delivery on your next order.", 8, "#e6e6e6"),
    ("Better Luck Next Time", "No prize this time. Spin again!", 30, "#9e9e9e"),
]

SCHEMA = """
create table if not exists prizes (
    id integer primary key autoincrement,
    name text not null,
    description text not null default '',
    weight integer not null,
    color text not null,
    sort_order integer not null default 0
);
create table if not exists wins (
    id integer primary key autoincrement,
    player text not null,
    prize_id integer not null,
    prize_name text not null,
    created_at text not null
);
create index if not exists wins_player_idx on wins(player, id);
"""


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    with closing(connect()) as conn, conn:
        conn.executescript(SCHEMA)
        count = conn.execute("select count(*) from prizes").fetchone()[0]
        if count == 0:
            conn.executemany(
                "insert into prizes (name, description, weight, color, sort_order) "
                "values (?, ?, ?, ?, ?)",
                [(n, d, w, c, i) for i, (n, d, w, c) in enumerate(SAMPLE_PRIZES)],
            )


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def clean_player(raw):
    name = re.sub(r"\s+", " ", str(raw or "")).strip()[:30]
    return name or "Guest"


def load_prizes(conn):
    rows = conn.execute(
        "select id, name, description, weight, color from prizes "
        "where weight > 0 order by sort_order, id"
    ).fetchall()
    return [dict(r) for r in rows]


def public_prizes(prizes):
    total = sum(p["weight"] for p in prizes) or 1
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "description": p["description"],
            "color": p["color"],
            "weight": p["weight"],
            "chance": round(100.0 * p["weight"] / total, 1),
        }
        for p in prizes
    ]


def win_row(row):
    return {
        "id": row["id"],
        "player": row["player"],
        "prize_name": row["prize_name"],
        "created_at": row["created_at"],
    }


def api_prizes():
    with closing(connect()) as conn:
        prizes = public_prizes(load_prizes(conn))
    return 200, {"prizes": prizes, "total_weight": sum(p["weight"] for p in prizes)}


def api_spin(body):
    player = clean_player(body.get("player"))
    with closing(connect()) as conn, conn:
        prizes = load_prizes(conn)
        if not prizes:
            return 409, {"error": "The wheel has no prizes yet."}
        index = random.choices(
            range(len(prizes)), weights=[p["weight"] for p in prizes]
        )[0]
        all_prizes = public_prizes(prizes)   # chances computed over the whole wheel
        prize = prizes[index]
        created = utc_now()
        cur = conn.execute(
            "insert into wins (player, prize_id, prize_name, created_at) "
            "values (?, ?, ?, ?)",
            (player, prize["id"], prize["name"], created),
        )
        win = {
            "id": cur.lastrowid,
            "player": player,
            "prize_name": prize["name"],
            "created_at": created,
        }
    return 200, {
        "index": index,
        "prize": all_prizes[index],
        "win": win,
    }


def api_records(query):
    raw = (query.get("player") or [""])[0]
    if not raw.strip():
        return 200, {"player": "", "wins": [], "total": 0}
    player = clean_player(raw)
    with closing(connect()) as conn:
        rows = conn.execute(
            "select id, player, prize_name, created_at from wins "
            "where player = ? collate nocase order by id desc limit 200",
            (player,),
        ).fetchall()
    wins = [win_row(r) for r in rows]
    return 200, {"player": player, "wins": wins, "total": len(wins)}


def api_recent():
    with closing(connect()) as conn:
        rows = conn.execute(
            "select id, player, prize_name, created_at from wins "
            "order by id desc limit 10"
        ).fetchall()
    return 200, {"wins": [win_row(r) for r in rows]}


class Handler(BaseHTTPRequestHandler):
    server_version = "WheelOfFortune/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def send_body(self, status, content_type, data, cache="no-store"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", cache)
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, status, payload):
        data = json.dumps(payload).encode("utf-8")
        self.send_body(status, "application/json; charset=utf-8", data)

    def send_text_page(self, status, message):
        html = (
            "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<title>Not found</title></head><body style=\"font-family:sans-serif\">"
            f"<h1>{message}</h1><p><a href=\"/\">Back to the wheel</a></p></body></html>"
        ).encode("utf-8")
        self.send_body(status, CONTENT_TYPES[".html"], html)

    def send_file(self, file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        ext = os.path.splitext(file_path)[1].lower()
        self.send_body(
            200,
            CONTENT_TYPES.get(ext, "application/octet-stream"),
            data,
            cache="no-cache",
        )

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path.rstrip("/") or "/"

        if path.startswith("/api/"):
            query = parse_qs(url.query)
            routes = {
                "/api/prizes": lambda: api_prizes(),
                "/api/records": lambda: api_records(query),
                "/api/recent": lambda: api_recent(),
            }
            route = routes.get(path)
            if route is None:
                return self.send_json(404, {"error": "Not found"})
            status, payload = route()
            return self.send_json(status, payload)

        if path in PAGES:
            return self.send_file(os.path.join(STATIC_DIR, PAGES[path]))

        if path.startswith("/static/"):
            full = os.path.normpath(
                os.path.join(STATIC_DIR, path[len("/static/"):])
            )
            if full.startswith(STATIC_DIR + os.sep) and os.path.isfile(full):
                return self.send_file(full)

        return self.send_text_page(404, "Page not found")

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        if path != "/api/spin":
            return self.send_json(404, {"error": "Not found"})
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length > 0 else b""
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except ValueError:
            return self.send_json(400, {"error": "Invalid JSON"})
        if not isinstance(body, dict):
            body = {}
        status, payload = api_spin(body)
        return self.send_json(status, payload)


def main():
    init_db()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Wheel of Fortune running at http://127.0.0.1:{PORT}", flush=True)
    print(f"Data directory: {DATA_DIR}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
