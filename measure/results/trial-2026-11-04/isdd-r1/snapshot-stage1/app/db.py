"""SQLite の接続と表の作成。

接続は自動コミットの状態で開き、書き込みを伴う処理は BEGIN IMMEDIATE で始めて
COMMIT か ROLLBACK で終える。これで同時更新を直列化し、記録の食い違いを防ぐ。
"""

import os
import sqlite3

DB_FILE = "isdd.sqlite3"

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    employee_number TEXT PRIMARY KEY
        CHECK (length(employee_number) = 6 AND employee_number NOT GLOB '*[^0-9]*'),
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    is_manager INTEGER NOT NULL CHECK (is_manager IN (0, 1))
);
CREATE TABLE IF NOT EXISTS equipment (
    equipment_number TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS loans (
    equipment_number TEXT PRIMARY KEY REFERENCES equipment (equipment_number),
    borrower_employee_number TEXT NOT NULL REFERENCES accounts (employee_number),
    lent_on TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    employee_number TEXT NOT NULL REFERENCES accounts (employee_number),
    last_seen REAL NOT NULL
);
"""


def connect(data_dir: str) -> sqlite3.Connection:
    """DATA_DIR の SQLite に接続する。外部キーを有効にし、ロック待ちは 5 秒まで。"""
    os.makedirs(data_dir, exist_ok=True)
    conn = sqlite3.connect(os.path.join(data_dir, DB_FILE), timeout=5, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """表が無ければ作る。既にあれば何もしない。"""
    conn.executescript(SCHEMA)
