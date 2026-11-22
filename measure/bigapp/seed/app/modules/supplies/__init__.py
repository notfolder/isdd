"""消耗品の申請。数量と税抜きの単価を記録し、承認または却下する。"""

from app.modules.supplies.web import bp

TITLE = "消耗品の申請"

SCHEMA = """
CREATE TABLE IF NOT EXISTS supplies_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_no TEXT NOT NULL REFERENCES employees(employee_no),
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    amount_incl_tax INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending'
);
"""

__all__ = ["bp", "TITLE", "SCHEMA"]
