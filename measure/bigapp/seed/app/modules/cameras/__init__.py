"""カメラの貸出。物の登録と、貸出・返却の記録を扱う。"""

from app.modules.cameras.views import bp

TITLE = "カメラの貸出"

SCHEMA = """
CREATE TABLE IF NOT EXISTS cameras_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cameras_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""

__all__ = ["bp", "TITLE", "SCHEMA"]
