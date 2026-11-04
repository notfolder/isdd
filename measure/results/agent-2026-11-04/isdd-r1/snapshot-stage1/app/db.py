"""SQLite の接続とテーブルの初期化。"""

import sqlite3
from pathlib import Path

DB_FILE_NAME = "app.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY,
    employee_number TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('manager', 'member'))
);
CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY,
    equipment_number TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    """自動トランザクションを使わない接続を開く。トランザクションは呼び出し側で BEGIN する。"""
    conn = sqlite3.connect(str(db_path), isolation_level=None, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(db_path: Path) -> None:
    """テーブルが無ければ作る。何度実行しても同じ状態になる。"""
    conn = connect(db_path)
    try:
        conn.executescript(SCHEMA)
    finally:
        conn.close()
