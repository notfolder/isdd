"""社員章（社章）の申請。申請・承認・却下を扱う。"""

from flask import Blueprint

bp = Blueprint("badges", __name__, url_prefix="/badges", template_folder="templates")
TITLE = "社章の申請"

SCHEMA = """
CREATE TABLE IF NOT EXISTS badges_request (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_no TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    amount_incl_tax INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL
);
"""

from app.modules.badges import routes  # noqa: E402,F401  (ルートの登録)
