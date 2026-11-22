"""タブレットの貸出。物の登録、貸出、返却、履歴を扱う。"""

from flask import Blueprint

TITLE = "タブレットの貸出"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tablets_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tablets_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""

bp = Blueprint("tablets", __name__, url_prefix="/tablets", template_folder="templates")

from app.modules.tablets import views  # noqa: E402,F401  ルートの登録のため
