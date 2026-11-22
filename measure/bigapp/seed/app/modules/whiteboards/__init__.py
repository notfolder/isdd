"""ホワイトボードの貸出。物の登録と、社員への貸出・返却を扱う。"""

from flask import Blueprint

TITLE = "ホワイトボードの貸出"

# 貸出の行は返却しても残す（returned_on が空のものが貸出中）。履歴のため物の削除後も残す。
SCHEMA = """
CREATE TABLE IF NOT EXISTS whiteboards_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS whiteboards_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""

bp = Blueprint("whiteboards", __name__, url_prefix="/whiteboards", template_folder="templates")

from app.modules.whiteboards import handlers  # noqa: E402,F401  ルートの登録
