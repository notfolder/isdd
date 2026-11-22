"""来客用飲料の申請。数量と税抜きの単価を記録し、税込みの金額を計算して承認・却下する（総務規程 第 5 条）。"""

from app.modules.beverages.views import bp

TITLE = "来客用飲料の申請"

SCHEMA = """
CREATE TABLE IF NOT EXISTS beverages_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_no TEXT NOT NULL REFERENCES employees(employee_no),
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    amount_incl_tax INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending'
);
"""

__all__ = ["bp", "TITLE", "SCHEMA"]
