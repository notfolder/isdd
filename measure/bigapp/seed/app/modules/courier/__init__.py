"""宅配便の申請。数量と税抜きの単価を記録し、承認か却下で決める。"""

from app.modules.courier.web import bp

TITLE = "宅配便の申請"

SCHEMA = """
CREATE TABLE IF NOT EXISTS courier_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_no TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    amount_incl_tax INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending',
    created_on TEXT NOT NULL
);
"""

__all__ = ["bp", "TITLE", "SCHEMA"]
