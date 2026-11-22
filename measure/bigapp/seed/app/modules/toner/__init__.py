"""トナーの申請。数量と税抜きの単価を記録し、承認または却下する（総務規程 第 5 条）。"""

from flask import Blueprint

bp = Blueprint("toner", __name__, url_prefix="/toner", template_folder="templates")
TITLE = "トナーの申請"

SCHEMA = """
CREATE TABLE IF NOT EXISTS toner_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_no TEXT NOT NULL REFERENCES employees(employee_no),
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    amount_excl_tax INTEGER NOT NULL,
    amount_incl_tax INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL
);
"""

from app.modules.toner import routes  # noqa: E402,F401  ルートを bp に登録する
