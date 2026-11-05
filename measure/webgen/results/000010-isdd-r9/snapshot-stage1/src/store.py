"""SQLite storage for prizes and winning records."""

import os
import sqlite3
from typing import Any, Dict, List

# Sample prizes inserted when the prize table is empty:
# (name, description, weight, is_win, position). Weights total 100.
SAMPLE_PRIZES = [
    ("10% Off Coupon", "10% off your next order", 15, 1, 1),
    ("Free Coffee", "One regular coffee", 10, 1, 2),
    ("Tote Bag", "A canvas tote bag", 8, 1, 3),
    ("$5 Gift Card", "A $5 gift card", 5, 1, 4),
    ("Free Shipping", "Free shipping on one order", 12, 1, 5),
    ("Mystery Gift", "A surprise gift", 5, 1, 6),
    ("Sticker Pack", "A set of stickers", 20, 1, 7),
    ("Better Luck Next Time", "No prize this time", 25, 0, 8),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS prizes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    weight INTEGER NOT NULL CHECK (weight BETWEEN 1 AND 100),
    is_win INTEGER NOT NULL CHECK (is_win IN (0, 1)),
    position INTEGER NOT NULL UNIQUE CHECK (position >= 1)
);
CREATE TABLE IF NOT EXISTS winning_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_key TEXT NOT NULL,
    display_name TEXT NOT NULL,
    prize_name TEXT NOT NULL,
    won_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_winning_records_player ON winning_records (player_key);
"""


class Store:
    """Reads and writes prizes and winning records in one SQLite file."""

    def __init__(self, db_path: str) -> None:
        directory = os.path.dirname(os.path.abspath(db_path))
        os.makedirs(directory, exist_ok=True)
        self._db_path = db_path
        conn = self._connect()
        try:
            conn.executescript(SCHEMA)
            conn.commit()
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        return conn

    def seed_sample_prizes(self) -> bool:
        """Insert the sample prizes when there are none. Returns True if inserted."""
        conn = self._connect()
        try:
            count = conn.execute("SELECT COUNT(*) FROM prizes").fetchone()[0]
            if count:
                return False
            conn.executemany(
                "INSERT INTO prizes (name, description, weight, is_win, position) "
                "VALUES (?, ?, ?, ?, ?)",
                SAMPLE_PRIZES,
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def list_prizes(self) -> List[Dict[str, Any]]:
        """Return all prizes in display order."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT id, name, description, weight, is_win, position "
                "FROM prizes ORDER BY position"
            ).fetchall()
        finally:
            conn.close()
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "weight": row["weight"],
                "is_win": bool(row["is_win"]),
                "position": row["position"],
            }
            for row in rows
        ]

    def add_winning(self, player_key: str, display_name: str, prize_name: str, won_at: str) -> int:
        """Record one winning. Returns the new record id."""
        conn = self._connect()
        try:
            cursor = conn.execute(
                "INSERT INTO winning_records (player_key, display_name, prize_name, won_at) "
                "VALUES (?, ?, ?, ?)",
                (player_key, display_name, prize_name, won_at),
            )
            conn.commit()
            return int(cursor.lastrowid)
        finally:
            conn.close()

    def list_winnings(self, player_key: str) -> List[Dict[str, Any]]:
        """Return the winning records of one player, newest first."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT id, display_name, prize_name, won_at FROM winning_records "
                "WHERE player_key = ? ORDER BY won_at DESC, id DESC",
                (player_key,),
            ).fetchall()
        finally:
            conn.close()
        return [dict(row) for row in rows]
