"""文具の申請。数量と税抜きの単価を記録し、税込みの金額を計算して、承認・却下を扱う。"""

from flask import Blueprint

TITLE = "文具の申請"

SCHEMA = """
CREATE TABLE IF NOT EXISTS stationery_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_no TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending'
);
"""

bp = Blueprint("stationery", __name__, url_prefix="/stationery", template_folder="templates")

from app.modules.stationery import handlers  # noqa: E402,F401  ルートの登録のため
