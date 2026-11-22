"""乗車券の申請。数量と税抜き単価を記録し、税込み金額を計算して承認・却下する。"""

from flask import Blueprint

TITLE = "乗車券の申請"

SCHEMA = """
CREATE TABLE IF NOT EXISTS train_tickets_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_no TEXT NOT NULL REFERENCES employees(employee_no),
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL
);
"""

bp = Blueprint("train_tickets", __name__, url_prefix="/train_tickets", template_folder="templates")

from app.modules.train_tickets import web  # noqa: E402,F401  ルートの登録
