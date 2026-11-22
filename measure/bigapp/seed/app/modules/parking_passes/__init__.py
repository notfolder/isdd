"""駐車許可証の貸出。"""

from app.modules.parking_passes.routes import bp

TITLE = "駐車許可証の貸出"

SCHEMA = """
CREATE TABLE IF NOT EXISTS parking_passes_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS parking_passes_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    item_name TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""

__all__ = ["bp", "TITLE", "SCHEMA"]
