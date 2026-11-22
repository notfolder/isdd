"""ケータリングの申請。数量と税抜き単価を記録し、承認または却下する。"""

from app.modules.catering.views import bp

TITLE = "ケータリングの申請"

SCHEMA = """
CREATE TABLE IF NOT EXISTS catering_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_no TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    amount_incl_tax INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending',
    requested_on TEXT NOT NULL
);
"""

__all__ = ["bp", "TITLE", "SCHEMA"]
