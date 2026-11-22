"""テントの貸出。物（テント）の台帳と、社員への貸出・返却を扱う。"""

from flask import Blueprint

bp = Blueprint("tents", __name__, url_prefix="/tents", template_folder="templates")
TITLE = "テントの貸出"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tents_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tents_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    item_name TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""

from app.modules.tents import views  # noqa: E402,F401  ルートの登録
