"""生花の申請。申請の記録と、承認・却下を扱う。"""

from flask import Blueprint

TITLE = "生花の申請"

SCHEMA = """
CREATE TABLE IF NOT EXISTS flowers_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_no TEXT NOT NULL REFERENCES employees(employee_no),
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending'
);
"""

bp = Blueprint("flowers", __name__, url_prefix="/flowers", template_folder="templates")

from app.modules.flowers import routes  # noqa: E402,F401  ルートを bp に登録するために読み込む
