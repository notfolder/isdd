"""SQLite の接続とスキーマの作成。"""

import sqlite3
from pathlib import Path

DB_FILE_NAME = "equipment_ledger.sqlite3"
BUSY_TIMEOUT_SECONDS = 5

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS accounts (
    employee_number TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('manager', 'employee')),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS equipment (
    equipment_number TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS lendings (
    equipment_number TEXT PRIMARY KEY REFERENCES equipment(equipment_number) ON UPDATE CASCADE,
    employee_number TEXT NOT NULL REFERENCES accounts(employee_number),
    lent_on TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    employee_number TEXT NOT NULL REFERENCES accounts(employee_number),
    last_seen REAL NOT NULL
);
"""


def connect(data_dir):
    """DATA_DIR の DB に接続する。

    data_dir が無ければ作る。自動コミットを無効にし、各処理が BEGIN IMMEDIATE で
    トランザクションを明示する。書き込みのロック待ちは 5 秒まで。
    引数 data_dir は Path。戻り値は sqlite3 の接続。
    """
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(
        Path(data_dir) / DB_FILE_NAME,
        timeout=BUSY_TIMEOUT_SECONDS,
        isolation_level=None,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn):
    """4 つのテーブル（アカウント、備品、貸出、セッション）が無ければ作る。

    引数 conn は connect の戻り値。既にあっても壊さない。
    """
    conn.executescript(SCHEMA_SQL)
