"""救急箱の貸出。物の登録、貸出、返却、履歴を扱う。"""

from flask import Blueprint

TITLE = "救急箱の貸出"

SCHEMA = """
CREATE TABLE IF NOT EXISTS first_aid_kits_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS first_aid_kits_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS first_aid_kits_one_open_loan
    ON first_aid_kits_loans (item_code) WHERE returned_on IS NULL;
"""

bp = Blueprint("first_aid_kits", __name__, url_prefix="/first_aid_kits", template_folder="templates")

from app.modules.first_aid_kits import handlers  # noqa: E402,F401  ルートを登録する
