#!/usr/bin/env python3
"""Wheel of Fortune: a small web server (Python standard library only).

Serves the pages in static/ and a JSON API under /api.
Data (SQLite) lives in $DATA_DIR/wheel.db. Sample prizes are added when the
prize table is empty, so the site works immediately with an empty DATA_DIR.
"""
import json
import os
import random
import sqlite3
import threading
from contextlib import closing
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
PORT = int(os.environ.get("PORT", "8000"))
DATA_DIR = os.path.abspath(os.environ.get("DATA_DIR") or os.path.join(BASE_DIR, "data"))
DB_PATH = os.path.join(DATA_DIR, "wheel.db")
MAX_NAME_LENGTH = 30
MAX_BODY_BYTES = 4096

PAGES = {
    "/": "index.html",
    "/prizes": "prizes.html",
    "/winnings": "winnings.html",
}

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
}

# name, description, weight, segment color, is_win
SAMPLE_PRIZES = [
    ("10% Off Coupon", "10% off your next order.", 20, "#8b0000", 1),
    ("Free Coffee", "One free regular coffee.", 15, "#a11d1d", 1),
    ("Movie Ticket", "One free movie ticket.", 10, "#5c0000", 1),
    ("Mystery Gift", "A surprise gift from the shop.", 5, "#a11d1d", 1),
    ("T-Shirt", "A premium cotton T-shirt.", 5, "#7d1414", 1),
    ("$50 Gift Card", "A $50 gift card.", 5, "#5c0000", 1),
    ("Try Again", "No prize this time. Spin again!", 40, "#555555", 0),
]

_lock = threading.Lock()
_rng = random.SystemRandom()


def connect():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(connect()) as db:
        with db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS prizes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    weight INTEGER NOT NULL CHECK (weight >= 0),
                    color TEXT NOT NULL,
                    is_win INTEGER NOT NULL DEFAULT 1,
                    sort_order INTEGER NOT NULL DEFAULT 0)"""
            )
            db.execute(
                """CREATE TABLE IF NOT EXISTS winnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player TEXT NOT NULL,
                    prize_id INTEGER,
                    prize_name TEXT NOT NULL,
                    created_at TEXT NOT NULL)"""
            )
            count = db.execute("SELECT COUNT(*) FROM prizes").fetchone()[0]
            if count == 0:
                for order, (name, desc, weight, color, is_win) in enumerate(SAMPLE_PRIZES):
                    db.execute(
                        "INSERT INTO prizes (name, description, weight, color, is_win, sort_order)"
                        " VALUES (?, ?, ?, ?, ?, ?)",
                        (name, desc, weight, color, is_win, order),
                    )


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def list_prizes(db):
    rows = db.execute("SELECT * FROM prizes ORDER BY sort_order, id").fetchall()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "description": r["description"],
            "weight": r["weight"],
            "color": r["color"],
            "is_win": bool(r["is_win"]),
        }
        for r in rows
    ]


def api_prizes():
    with closing(connect()) as db:
        prizes = list_prizes(db)
    total = sum(p["weight"] for p in prizes)
    for p in prizes:
        p["chance"] = round(100.0 * p["weight"] / total, 1) if total else 0.0
    return {"prizes": prizes, "total_weight": total}


def spin(player):
    """Pick one segment by weight. Wins are recorded for the player."""
    with _lock:
        with closing(connect()) as db:
            with db:
                prizes = list_prizes(db)
                weights = [p["weight"] for p in prizes]
                if not prizes or sum(weights) <= 0:
                    raise RuntimeError("No prizes are set up yet.")
                index = _rng.choices(range(len(prizes)), weights=weights)[0]
                prize = prizes[index]
                if prize["is_win"]:
                    db.execute(
                        "INSERT INTO winnings (player, prize_id, prize_name, created_at)"
                        " VALUES (?, ?, ?, ?)",
                        (player, prize["id"], prize["name"], now_iso()),
                    )
    return {"index": index, "prize": prize, "won": prize["is_win"]}


def api_winnings(player):
    with closing(connect()) as db:
        if player:
            rows = db.execute(
                "SELECT id, player, prize_name, created_at FROM winnings"
                " WHERE player = ? COLLATE NOCASE ORDER BY id DESC LIMIT 200",
                (player,),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT id, player, prize_name, created_at FROM winnings"
                " ORDER BY id DESC LIMIT 20"
            ).fetchall()
    return {"winnings": [dict(r) for r in rows]}


class Handler(BaseHTTPRequestHandler):
    server_version = "WheelOfFortune/1.0"

    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, full):
        with open(full, "rb") as f:
            body = f.read()
        ext = os.path.splitext(full)[1].lower()
        self.send_response(200)
        self.send_header("Content-Type", CONTENT_TYPES.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path if url.path == "/" else url.path.rstrip("/")
        if path == "/api/prizes":
            return self.send_json(200, api_prizes())
        if path == "/api/winnings":
            player = parse_qs(url.query).get("player", [""])[0].strip()
            return self.send_json(200, api_winnings(player))
        if path in PAGES:
            return self.send_file(os.path.join(STATIC_DIR, PAGES[path]))
        if path.startswith("/static/"):
            full = os.path.realpath(os.path.join(STATIC_DIR, path[len("/static/"):]))
            if full.startswith(os.path.realpath(STATIC_DIR) + os.sep) and os.path.isfile(full):
                return self.send_file(full)
        return self.send_json(404, {"error": "Not found."})

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        if path != "/api/spin":
            return self.send_json(404, {"error": "Not found."})
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if length < 0 or length > MAX_BODY_BYTES:
            return self.send_json(400, {"error": "Invalid request."})
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return self.send_json(400, {"error": "Invalid request."})
        player = str(data.get("player", "")).strip() if isinstance(data, dict) else ""
        if not player:
            return self.send_json(400, {"error": "Please enter your name before spinning."})
        if len(player) > MAX_NAME_LENGTH:
            return self.send_json(400, {"error": "Your name must be %d characters or fewer." % MAX_NAME_LENGTH})
        try:
            result = spin(player)
        except RuntimeError as exc:
            return self.send_json(500, {"error": str(exc)})
        return self.send_json(200, result)


def main():
    init_db()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("Wheel of Fortune running at http://127.0.0.1:%d (data: %s)" % (PORT, DATA_DIR), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
