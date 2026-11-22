"""台車の貸出。台車の登録、貸出、返却、履歴を扱う。"""

from app.modules.carts.routes import bp  # noqa: F401

TITLE = "台車の貸出"

SCHEMA = """
CREATE TABLE IF NOT EXISTS carts_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS carts_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""
