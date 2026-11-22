"""来客用入館証の貸出。"""

from app.modules.guest_badges.web import bp

TITLE = "来客用入館証の貸出"

SCHEMA = """
CREATE TABLE IF NOT EXISTS guest_badges_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS guest_badges_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""

__all__ = ["bp", "TITLE", "SCHEMA"]
