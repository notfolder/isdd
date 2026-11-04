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
    name TEXT NOT NULL,
    revision INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY,
    equipment_id INTEGER NOT NULL UNIQUE REFERENCES equipment(id),
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    lent_on TEXT NOT NULL
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    """自動トランザクションを使わない接続を開く。トランザクションは呼び出し側で BEGIN する。"""
    conn = sqlite3.connect(str(db_path), isolation_level=None, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(db_path: Path) -> None:
    """テーブルが無ければ作る。版番号の列が無い既存の DB には列を足す。何度実行しても同じ状態になる。"""
    conn = connect(db_path)
    try:
        conn.executescript(SCHEMA)
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(equipment)")}
        if "revision" not in columns:
            conn.execute("ALTER TABLE equipment ADD COLUMN revision INTEGER NOT NULL DEFAULT 1")
    finally:
        conn.close()
