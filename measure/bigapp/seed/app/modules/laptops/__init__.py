"""ノート PC の貸出。物の登録と、社員への貸出・返却を扱う。"""

from flask import Blueprint

TITLE = "ノート PC の貸出"

SCHEMA = """
CREATE TABLE IF NOT EXISTS laptops_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS laptops_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    item_name TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""

bp = Blueprint("laptops", __name__, url_prefix="/laptops", template_folder="templates")

from app.modules.laptops import routes  # noqa: E402,F401  ルートの登録のため
