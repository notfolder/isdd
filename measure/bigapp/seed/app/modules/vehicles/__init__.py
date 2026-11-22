"""社用車の貸出。貸出期間は 3 日、1 人が同時に借りられるのは 1 件まで。"""

from flask import Blueprint

TITLE = "社用車の貸出"

SCHEMA = """
CREATE TABLE IF NOT EXISTS vehicles_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS vehicles_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""

bp = Blueprint("vehicles", __name__, url_prefix="/vehicles", template_folder="templates")

from app.modules.vehicles import routes  # noqa: E402,F401  ルートの登録のために読み込む
