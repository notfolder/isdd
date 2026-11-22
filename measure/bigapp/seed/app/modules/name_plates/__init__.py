"""名札の申請。数量と税抜き単価を記録し、税込みの金額を計算して、承認・却下を扱う。"""

from flask import Blueprint

TITLE = "名札の申請"

bp = Blueprint("name_plates", __name__, url_prefix="/name_plates", template_folder="templates")

SCHEMA = """
CREATE TABLE IF NOT EXISTS name_plates_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_no TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending'
);
"""

from . import web  # noqa: E402,F401  ルートを bp に登録する
