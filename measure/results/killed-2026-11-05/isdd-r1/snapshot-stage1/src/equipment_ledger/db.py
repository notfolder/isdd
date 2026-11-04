"""SQLite の接続と初期化。リクエストごとの接続を Flask の g に持つ。"""

import sqlite3
from pathlib import Path

from flask import current_app, g

DATABASE_FILE = "equipment.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_number TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_number TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('manager', 'employee'))
);
"""


def connect_database(data_dir):
    """データ格納先の SQLite ファイルへ接続する。

    トランザクションは呼び出し側が BEGIN と COMMIT で明示する（autocommit モード）。
    書き込みの競合は busy_timeout で待つ。外部キー制約を有効にする。
    """
    path = Path(data_dir) / DATABASE_FILE
    conn = sqlite3.connect(path, timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


def initialize_database(conn):
    """備品とアカウントのテーブルを作る。既にあれば何もしない。"""
    conn.executescript(SCHEMA)


def get_db():
    """現在のリクエストの DB 接続を返す。無ければ開く。"""
    if "db" not in g:
        g.db = connect_database(current_app.config["DATA_DIR"])
    return g.db


def close_db(_exception=None):
    """リクエストの終わりに DB 接続を閉じる。"""
    db = g.pop("db", None)
    if db is not None:
        db.close()
