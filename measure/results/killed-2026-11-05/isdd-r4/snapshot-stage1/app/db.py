"""SQLite の接続と初期化。"""

import os
import secrets
import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_number TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 30),
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('manager', 'employee'))
);
CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_number TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 50)
);
"""

BUSY_TIMEOUT_SECONDS = 5


def get_db():
    """この要求の DB 接続を返す。無ければ作る。

    書き込みは各関数が明示のトランザクションで行うため、自動コミットにしておく。
    """
    if "db" not in g:
        conn = sqlite3.connect(
            current_app.config["DB_PATH"],
            timeout=BUSY_TIMEOUT_SECONDS,
            isolation_level=None,
        )
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


def close_db(exc=None):
    """要求の終わりに DB 接続を閉じる。"""
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db(app):
    """テーブルを作って WAL モードにする。秘密鍵ファイルが無ければ作り、アプリの設定に入れる。

    引数: app（DB_PATH と DATA_DIR を設定済みの Flask アプリ）。
    """
    conn = sqlite3.connect(app.config["DB_PATH"], timeout=BUSY_TIMEOUT_SECONDS, isolation_level=None)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(SCHEMA)
    finally:
        conn.close()

    key_path = os.path.join(app.config["DATA_DIR"], "secret_key")
    if not os.path.exists(key_path):
        try:
            fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            fd = None
        if fd is not None:
            with os.fdopen(fd, "w") as f:
                f.write(secrets.token_hex(32))
    with open(key_path) as f:
        app.config["SECRET_KEY"] = f.read().strip()
