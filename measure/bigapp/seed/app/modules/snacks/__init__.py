"""茶菓の申請。数量と税抜き単価を記録し、承認・却下を扱う。"""

from flask import Blueprint

TITLE = "茶菓の申請"

SCHEMA = """
CREATE TABLE IF NOT EXISTS snacks_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_no TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    amount_incl_tax INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending'
);
"""

bp = Blueprint("snacks", __name__, url_prefix="/snacks", template_folder="templates")

from app.modules.snacks import views  # noqa: E402,F401  ルートの登録のために読み込む
