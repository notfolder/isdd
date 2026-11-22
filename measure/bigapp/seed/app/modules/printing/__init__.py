"""印刷の申請。数量と税抜き単価を記録し、承認か却下をする（総務規程 第 5 条）。"""

from flask import Blueprint

TITLE = "印刷の申請"

bp = Blueprint("printing", __name__, url_prefix="/printing", template_folder="templates")

SCHEMA = """
CREATE TABLE IF NOT EXISTS printing_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_no TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending'
);
"""

from app.modules.printing import handlers  # noqa: E402,F401  ルートの登録のために読み込む
