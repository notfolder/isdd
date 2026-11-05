"""SQLite によるデータ層: 表の作成、初期データ、景品と当選記録の問い合わせ。"""

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

SAMPLE_PRIZES = [
    ("Free Coffee", "One cup of coffee at the counter"),
    ("Free Dessert", "One dessert of your choice"),
    ("10% Off Coupon", "10% off your next purchase"),
    ("Free Tote Bag", "A cloth tote bag"),
    ("Movie Ticket Pair", "Two tickets for a movie"),
    ("Mystery Gift", "A surprise gift from the staff"),
]

# (名前, 景品名, 何時間前に当選したか)
SAMPLE_RECORDS = [
    ("Sample Player", "Free Coffee", 3),
    ("Sample Player", "Free Dessert", 2),
    ("Sample Player", "10% Off Coupon", 1),
]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS prizes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS winning_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    prize_id INTEGER NOT NULL REFERENCES prizes(id),
    prize_name TEXT NOT NULL,
    won_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_winning_records_name
    ON winning_records (player_name COLLATE NOCASE, won_at);
"""


def _utc_text(moment: datetime) -> str:
    """UTC の ISO 8601 文字列（秒まで、末尾は Z）に変換する。"""
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Database:
    """景品と当選記録を保存する SQLite ファイルへの窓口。要求ごとに接続を開いて閉じる。"""

    def __init__(self, path: str) -> None:
        self._path = path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        """表を作り、景品の表が空のときだけ初期データを入れる。"""
        conn = self._connect()
        try:
            conn.executescript(_SCHEMA)
            count = conn.execute("SELECT COUNT(*) FROM prizes").fetchone()[0]
            if count == 0:
                now = datetime.now(timezone.utc)
                with conn:
                    for order, (name, description) in enumerate(SAMPLE_PRIZES, start=1):
                        conn.execute(
                            "INSERT INTO prizes (name, description, sort_order) VALUES (?, ?, ?)",
                            (name, description, order),
                        )
                    prize_ids = {
                        row["name"]: row["id"]
                        for row in conn.execute("SELECT id, name FROM prizes")
                    }
                    for player, prize_name, hours_ago in SAMPLE_RECORDS:
                        conn.execute(
                            "INSERT INTO winning_records (player_name, prize_id, prize_name, won_at) "
                            "VALUES (?, ?, ?, ?)",
                            (
                                player,
                                prize_ids[prize_name],
                                prize_name,
                                _utc_text(now - timedelta(hours=hours_ago)),
                            ),
                        )
        finally:
            conn.close()

    def list_prizes(self) -> List[Dict[str, Any]]:
        """全景品を表示順（表示順、景品ID の昇順）で返す。"""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT id, name, description FROM prizes ORDER BY sort_order, id"
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def add_winning_record(self, player_name: str, prize: Dict[str, Any]) -> Dict[str, Any]:
        """当選記録を 1 件追加し、保存した記録を返す。当選日時は現在の UTC。"""
        won_at = _utc_text(datetime.now(timezone.utc))
        conn = self._connect()
        try:
            with conn:
                cursor = conn.execute(
                    "INSERT INTO winning_records (player_name, prize_id, prize_name, won_at) "
                    "VALUES (?, ?, ?, ?)",
                    (player_name, prize["id"], prize["name"], won_at),
                )
                record_id = cursor.lastrowid
            return {
                "id": record_id,
                "player_name": player_name,
                "prize_id": prize["id"],
                "prize_name": prize["name"],
                "won_at": won_at,
            }
        finally:
            conn.close()

    def list_winnings_by_name(self, player_name: str) -> List[Dict[str, Any]]:
        """名前の完全一致（大文字小文字を区別しない）で当選記録を絞り込み、新しい順に返す。

        各行は記録ID、名前、景品ID、景品名、当選日時を持つ。
        """
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT id, player_name, prize_id, prize_name, won_at FROM winning_records "
                "WHERE player_name = ? COLLATE NOCASE "
                "ORDER BY won_at DESC, id DESC",
                (player_name,),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
