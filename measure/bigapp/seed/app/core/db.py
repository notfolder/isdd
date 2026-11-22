"""SQLite への接続。リクエストごとに 1 本。"""

import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash

CORE_SCHEMA = """
CREATE TABLE IF NOT EXISTS employees (
    employee_no TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    dept TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT 'employee',
    status TEXT NOT NULL DEFAULT 'active',
    password_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    logged_at TEXT NOT NULL,
    actor_no TEXT,
    module TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT NOT NULL DEFAULT ''
);
"""

ADMIN_NO = "900001"
ADMIN_PASSWORD = "adminpass"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db(module_schemas):
    conn = get_db()
    conn.executescript(CORE_SCHEMA)
    for schema in module_schemas:
        conn.executescript(schema)
    if conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO employees (employee_no, name, dept, role, status, password_hash) VALUES (?, ?, ?, 'staff', 'active', ?)",
            (ADMIN_NO, "総務 管理", "総務部", generate_password_hash(ADMIN_PASSWORD)),
        )
    conn.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
