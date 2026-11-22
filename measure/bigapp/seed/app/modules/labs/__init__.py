"""実験室の予約。"""

from flask import Blueprint

TITLE = "実験室の予約"

SCHEMA = """
CREATE TABLE IF NOT EXISTS labs_rooms (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS labs_bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code TEXT NOT NULL REFERENCES labs_rooms(code),
    employee_no TEXT NOT NULL,
    date TEXT NOT NULL,
    start TEXT NOT NULL,
    "end" TEXT NOT NULL,
    cancelled INTEGER NOT NULL DEFAULT 0
);
"""

bp = Blueprint("labs", __name__, url_prefix="/labs", template_folder="templates")

from app.modules.labs import web  # noqa: E402,F401  ルートの登録のため
