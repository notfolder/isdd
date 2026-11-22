"""鍵の貸出。物（鍵など）の登録と、社員への貸出・返却を扱う。"""

from flask import Blueprint

TITLE = "鍵の貸出"

SCHEMA = """
CREATE TABLE IF NOT EXISTS keys_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS keys_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""

bp = Blueprint("keys", __name__, url_prefix="/keys", template_folder="templates")

from app.modules.keys import web  # noqa: E402,F401  ルートの登録
