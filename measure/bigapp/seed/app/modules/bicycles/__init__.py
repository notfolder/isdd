"""社用自転車の貸出。"""

from flask import Blueprint

TITLE = "社用自転車の貸出"

SCHEMA = """
CREATE TABLE IF NOT EXISTS bicycles_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS bicycles_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""

bp = Blueprint("bicycles", __name__, url_prefix="/bicycles", template_folder="templates")

from app.modules.bicycles import handlers  # noqa: E402,F401  ルートの登録
