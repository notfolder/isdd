"""SQLite への接続と、テーブルの用意。"""

import sqlite3
from contextlib import contextmanager
from typing import Iterator

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS prizes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 40),
    description TEXT NOT NULL CHECK (length(description) BETWEEN 1 AND 120),
    weight INTEGER NOT NULL CHECK (weight BETWEEN 1 AND 100),
    is_miss INTEGER NOT NULL CHECK (is_miss IN (0, 1)),
    position INTEGER NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS winning_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL CHECK (length(player_name) BETWEEN 1 AND 20),
    prize_id INTEGER NOT NULL REFERENCES prizes (id),
    prize_name TEXT NOT NULL CHECK (length(prize_name) BETWEEN 1 AND 40),
    won_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_winning_records_player ON winning_records (player_name);
"""


class Database:
    """SQLite ファイルを指す。接続は操作ごとに開いて閉じる（HTTP の別スレッドと共有しない）。"""

    def __init__(self, path: str) -> None:
        self._path = path

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """接続を開き、正常終了なら commit、例外なら rollback して閉じる。"""
        conn = sqlite3.connect(self._path, timeout=5)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        """テーブルと索引が無ければ作る。"""
        conn = sqlite3.connect(self._path, timeout=5)
        try:
            conn.executescript(SCHEMA_SQL)
            conn.commit()
        finally:
            conn.close()
