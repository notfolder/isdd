#!/usr/bin/env python3
"""Wheel of Fortune web server (standard library only).

Environment variables:
  PORT      port to listen on (default 8000), bound to 127.0.0.1
  DATA_DIR  directory for the SQLite database (default ./data), created if missing
"""
import datetime
import json
import mimetypes
import os
import secrets
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = Path(os.environ.get("DATA_DIR") or BASE_DIR / "data").resolve()
PORT = int(os.environ.get("PORT") or 8000)
DB_PATH = DATA_DIR / "wheel.db"
DB_LOCK = threading.Lock()
MAX_NAME_LENGTH = 40
MAX_RECORDS_RETURNED = 500

# Sample rewards inserted only when the database has no rewards yet.
# weight = relative chance; the displayed chance is weight / total weight.
SAMPLE_REWARDS = [
    ("Grand Reward: $100 Gift Card", "A $100 gift card for our online shop.", 1),
    ("Movie Tickets (2)", "Two tickets to any show in the next month.", 3),
    ("Free Coffee", "One free coffee of any size.", 10),
    ("20% Off Coupon", "20% off your next purchase.", 8),
    ("Free Shipping", "Free shipping on your next order.", 6),
    ("Mystery Gift Box", "A surprise box of goodies.", 2),
    ("Sticker Pack", "A pack of limited-edition stickers.", 15),
    ("Better Luck Next Time", "No reward this time. Spin again!", 20),
]


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def migrate_old_schema(conn):
    """Bring a database created by an earlier version up to the current names."""
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    if "prizes" in tables and "rewards" not in tables:
        conn.execute("ALTER TABLE prizes RENAME TO rewards")
    if "records" in tables:
        columns = {r[1] for r in conn.execute("PRAGMA table_info(records)")}
        if "prize_id" in columns:
            conn.execute("ALTER TABLE records RENAME COLUMN prize_id TO reward_id")
        if "prize_name" in columns:
            conn.execute("ALTER TABLE records RENAME COLUMN prize_name TO reward_name")
    conn.commit()


def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = connect()
    try:
        migrate_old_schema(conn)
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                weight INTEGER NOT NULL CHECK (weight > 0)
            );
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                reward_id INTEGER NOT NULL,
                reward_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_records_user
                ON records (user_name COLLATE NOCASE);
            """
        )
        # Data saved by the earlier wording is rewritten once so that existing
        # rewards and records also show "reward".
        for table, column in (
            ("rewards", "name"),
            ("rewards", "description"),
            ("records", "reward_name"),
        ):
            conn.execute(
                "UPDATE %s SET %s = REPLACE(REPLACE(%s, 'Prize', 'Reward'), 'prize', 'reward')"
                " WHERE %s LIKE '%%prize%%' OR %s LIKE '%%Prize%%'"
                % (table, column, column, column, column)
            )
        count = conn.execute("SELECT COUNT(*) FROM rewards").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO rewards (name, description, weight) VALUES (?, ?, ?)",
                SAMPLE_REWARDS,
            )
        conn.commit()
    finally:
        conn.close()


def clean_name(value):
    if not isinstance(value, str):
        return None
    name = " ".join(value.split())
    if not name or len(name) > MAX_NAME_LENGTH:
        return None
    return name


def reward_rows(conn):
    return [
        dict(r)
        for r in conn.execute(
            "SELECT id, name, description, weight FROM rewards ORDER BY id"
        )
    ]


class Handler(BaseHTTPRequestHandler):
    server_version = "WheelOfFortune/1.0"

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)

    # ---- helpers -------------------------------------------------------
    def send_bytes(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_bytes(status, body, "application/json; charset=utf-8")

    def send_error_json(self, status, message):
        self.send_json(status, {"error": message})

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length > 0 else b""
        if not raw:
            return {}
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        return data if isinstance(data, dict) else None

    # ---- routing -------------------------------------------------------
    def do_GET(self):
        url = urlparse(self.path)
        if url.path.startswith("/api/"):
            return self.handle_api_get(url.path, parse_qs(url.query))
        return self.serve_static(url.path)

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/spin":
            return self.handle_spin()
        self.send_error_json(404, "Not found")

    def handle_api_get(self, path, query):
        if path == "/api/rewards":
            return self.handle_rewards()
        if path == "/api/records":
            return self.handle_records(query)
        self.send_error_json(404, "Not found")

    # ---- API -----------------------------------------------------------
    def handle_rewards(self):
        with DB_LOCK:
            conn = connect()
            try:
                rewards = reward_rows(conn)
            finally:
                conn.close()
        total = sum(p["weight"] for p in rewards) or 1
        for p in rewards:
            p["chance"] = round(p["weight"] * 100.0 / total, 1)
        self.send_json(200, {"rewards": rewards})

    def handle_spin(self):
        body = self.read_json()
        if body is None:
            return self.send_error_json(400, "Invalid JSON body")
        name = clean_name(body.get("name"))
        if not name:
            return self.send_error_json(
                400, "Please enter a name (1-%d characters)." % MAX_NAME_LENGTH
            )
        with DB_LOCK:
            conn = connect()
            try:
                rewards = reward_rows(conn)
                if not rewards:
                    return self.send_error_json(409, "No rewards are configured.")
                rng = secrets.SystemRandom()
                chosen = rng.choices(
                    rewards, weights=[p["weight"] for p in rewards], k=1
                )[0]
                created = utc_now()
                cur = conn.execute(
                    "INSERT INTO records (user_name, reward_id, reward_name, created_at)"
                    " VALUES (?, ?, ?, ?)",
                    (name, chosen["id"], chosen["name"], created),
                )
                conn.commit()
                record = {
                    "id": cur.lastrowid,
                    "user_name": name,
                    "reward_id": chosen["id"],
                    "reward_name": chosen["name"],
                    "created_at": created,
                }
            finally:
                conn.close()
        self.send_json(
            200,
            {
                "reward": {
                    "id": chosen["id"],
                    "name": chosen["name"],
                    "description": chosen["description"],
                },
                "record": record,
            },
        )

    def handle_records(self, query):
        name = clean_name((query.get("name") or [""])[0])
        if not name:
            return self.send_error_json(400, "Please provide a name.")
        with DB_LOCK:
            conn = connect()
            try:
                rows = conn.execute(
                    "SELECT id, user_name, reward_id, reward_name, created_at"
                    " FROM records WHERE user_name = ? COLLATE NOCASE"
                    " ORDER BY id DESC LIMIT ?",
                    (name, MAX_RECORDS_RETURNED),
                ).fetchall()
                total = conn.execute(
                    "SELECT COUNT(*) FROM records WHERE user_name = ? COLLATE NOCASE",
                    (name,),
                ).fetchone()[0]
            finally:
                conn.close()
        self.send_json(
            200,
            {
                "name": name,
                "total": total,
                "records": [dict(r) for r in rows],
            },
        )

    # ---- static files --------------------------------------------------
    def serve_static(self, path):
        rel = path.lstrip("/") or "index.html"
        target = (STATIC_DIR / rel).resolve()
        try:
            target.relative_to(STATIC_DIR.resolve())
        except ValueError:
            return self.send_error_json(404, "Not found")
        if target.is_dir():
            target = target / "index.html"
        if not target.is_file():
            return self.send_error_json(404, "Not found")
        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript",):
            ctype += "; charset=utf-8"
        self.send_bytes(200, target.read_bytes(), ctype)


def main():
    init_db()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(
        "Wheel of Fortune running at http://127.0.0.1:%d (data: %s)"
        % (PORT, DATA_DIR),
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
