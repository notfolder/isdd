#!/usr/bin/env python3
"""Wheel of Fortune: a small web server (Python standard library only).

Serves the pages in static/ and a JSON API under /api.
Data (SQLite) lives in $DATA_DIR/wheel.db. Sample prizes are added when the
prize table is empty, so the site works immediately with an empty DATA_DIR.
"""
import json
import os
import random
import re
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
    "/manage": "manage.html",
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

# Segment colors (dark green shades; neighbours differ). Shown in order of the prize list.
PRIZE_PALETTE = ["#006400", "#1e5a1e", "#00703c", "#0b4f2a", "#2f6b2f", "#004d2c"]
NO_PRIZE_COLOR = "#4f6150"
DEFAULT_WEIGHT = 10

# name, description, weight, segment color, is_win
SAMPLE_PRIZES = [
    ("10% Off Coupon", "10% off your next order.", 20, "#006400", 1),
    ("Free Coffee", "One free regular coffee.", 15, "#1e5a1e", 1),
    ("Movie Ticket", "One free movie ticket.", 10, "#00703c", 1),
    ("Mystery Gift", "A surprise gift from the shop.", 5, "#0b4f2a", 1),
    ("T-Shirt", "A premium cotton T-shirt.", 5, "#2f6b2f", 1),
    ("$50 Gift Card", "A $50 gift card.", 5, "#004d2c", 1),
    ("Try Again", "No prize this time. Spin again!", 40, "#4f6150", 0),
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
            db.execute(
                """CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL)"""
            )
            seeded = db.execute("SELECT 1 FROM meta WHERE key = 'seeded'").fetchone()
            count = db.execute("SELECT COUNT(*) FROM prizes").fetchone()[0]
            if not seeded:
                # Sample prizes are added only once, so that a list emptied by the user stays empty.
                db.execute("INSERT INTO meta (key, value) VALUES ('seeded', '1')")
                for order, (name, desc, weight, color, is_win) in enumerate(SAMPLE_PRIZES):
                    db.execute(
                        "INSERT INTO prizes (name, description, weight, color, is_win, sort_order)"
                        " VALUES (?, ?, ?, ?, ?, ?)",
                        (name, desc, weight, color, is_win, order),
                    )


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def segment_color(index, is_win):
    if not is_win:
        return NO_PRIZE_COLOR
    return PRIZE_PALETTE[index % len(PRIZE_PALETTE)]


def list_prizes(db):
    rows = db.execute("SELECT * FROM prizes ORDER BY sort_order, id").fetchall()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "description": r["description"],
            "weight": r["weight"],
            "color": segment_color(i, bool(r["is_win"])),
            "is_win": bool(r["is_win"]),
        }
        for i, r in enumerate(rows)
    ]


def add_prize(name):
    """Add a prize (a winning segment) at the end of the list. Returns the new prize id."""
    with _lock:
        with closing(connect()) as db:
            with db:
                dup = db.execute(
                    "SELECT 1 FROM prizes WHERE name = ? COLLATE NOCASE", (name,)
                ).fetchone()
                if dup:
                    raise ValueError("A prize named \"%s\" is already on the list." % name)
                order = db.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 FROM prizes").fetchone()[0]
                cur = db.execute(
                    "INSERT INTO prizes (name, description, weight, color, is_win, sort_order)"
                    " VALUES (?, ?, ?, ?, 1, ?)",
                    (name, "", DEFAULT_WEIGHT, PRIZE_PALETTE[0], order),
                )
                return cur.lastrowid


def delete_prize(prize_id):
    """Remove a prize from the list. Past winnings keep the prize name. Returns False if not found."""
    with _lock:
        with closing(connect()) as db:
            with db:
                cur = db.execute("DELETE FROM prizes WHERE id = ?", (prize_id,))
                return cur.rowcount > 0


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


def delete_all_winnings():
    """Delete every winning record. Returns how many were deleted."""
    with _lock:
        with closing(connect()) as db:
            with db:
                cur = db.execute("DELETE FROM winnings")
                return cur.rowcount


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

    def read_json_body(self):
        """Return the parsed JSON body, or None if it is missing or invalid (the error is sent)."""
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if length < 0 or length > MAX_BODY_BYTES:
            self.send_json(400, {"error": "Invalid request."})
            return None
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            self.send_json(400, {"error": "Invalid request."})
            return None

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        if path == "/api/prizes":
            return self.handle_add_prize()
        if path != "/api/spin":
            return self.send_json(404, {"error": "Not found."})
        data = self.read_json_body()
        if data is None:
            return
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

    def handle_add_prize(self):
        data = self.read_json_body()
        if data is None:
            return
        name = str(data.get("name", "")).strip() if isinstance(data, dict) else ""
        if not name:
            return self.send_json(400, {"error": "Please enter a prize name."})
        if len(name) > MAX_NAME_LENGTH:
            return self.send_json(400, {"error": "The prize name must be %d characters or fewer." % MAX_NAME_LENGTH})
        try:
            new_id = add_prize(name)
        except ValueError as exc:
            return self.send_json(409, {"error": str(exc)})
        return self.send_json(201, {"id": new_id, "name": name})

    def do_DELETE(self):
        path = urlparse(self.path).path.rstrip("/")
        if path == "/api/winnings":
            return self.send_json(200, {"deleted": delete_all_winnings()})
        match = re.fullmatch(r"/api/prizes/(\d+)", path)
        if not match:
            return self.send_json(404, {"error": "Not found."})
        if not delete_prize(int(match.group(1))):
            return self.send_json(404, {"error": "That prize is no longer on the list."})
        return self.send_json(200, {"deleted": True})


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
