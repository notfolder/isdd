"""SQLite への接続とスキーマの初期化。"""

import os
import sqlite3

DB_FILE_NAME = "equipment_ledger.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS equipment (
    equipment_number TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    revision INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS account (
    employee_number TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('manager', 'member'))
);
CREATE TABLE IF NOT EXISTS lending (
    equipment_number TEXT PRIMARY KEY NOT NULL,
    employee_number TEXT NOT NULL,
    lent_on TEXT NOT NULL
);
"""


def open_connection(data_dir: str) -> sqlite3.Connection:
    """DB ファイルを開く。WAL モードと 5 秒の busy timeout を設定し、自動コミットにする。"""
    os.makedirs(data_dir, exist_ok=True)
    conn = sqlite3.connect(os.path.join(data_dir, DB_FILE_NAME), timeout=5, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def initialize_schema(conn: sqlite3.Connection) -> None:
    """3 テーブルを作る（無ければ）。版番号の列が無い旧い備品テーブルには列を足す。"""
    conn.executescript(SCHEMA_SQL)
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(equipment)").fetchall()}
    if "revision" not in columns:
        conn.execute("ALTER TABLE equipment ADD COLUMN revision INTEGER NOT NULL DEFAULT 0")
