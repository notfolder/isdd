"""SQLite の接続とスキーマの作成。

接続は自動コミットモードで開き、書き込みのトランザクションは呼び出し側が
BEGIN IMMEDIATE で明示的に始める。WAL と busy タイムアウトで同時の読み書きを待たせる。
"""

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    employee_number TEXT PRIMARY KEY CHECK (length(employee_number) = 6 AND employee_number NOT GLOB '*[^0-9]*'),
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('manager', 'member'))
);
CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_number TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS lendings (
    equipment_id INTEGER PRIMARY KEY REFERENCES equipment(id),
    employee_number TEXT NOT NULL REFERENCES accounts(employee_number),
    lent_on TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    employee_number TEXT NOT NULL REFERENCES accounts(employee_number),
    last_seen INTEGER NOT NULL
);
"""


def open_connection(db_path: Path) -> sqlite3.Connection:
    """DB に接続する。WAL、外部キー、busy タイムアウトを有効にする。

    Args:
        db_path: DB ファイルの場所。無ければ親ディレクトリごと作る。

    Returns:
        自動コミットモードの接続。呼び出し側が閉じる。
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=5, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def initialize_schema(db_path: Path) -> None:
    """スキーマを作る。既にあれば何もしない。

    Args:
        db_path: DB ファイルの場所。
    """
    conn = open_connection(db_path)
    try:
        conn.executescript(SCHEMA)
    finally:
        conn.close()
