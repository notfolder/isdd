"""ラウンジの貸切の予約。"""

from flask import Blueprint

TITLE = "ラウンジの貸切の予約"

SCHEMA = """
CREATE TABLE IF NOT EXISTS lounges_rooms (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS lounges_bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code TEXT NOT NULL REFERENCES lounges_rooms(code),
    employee_no TEXT NOT NULL,
    date TEXT NOT NULL,
    start TEXT NOT NULL,
    end TEXT NOT NULL,
    cancelled INTEGER NOT NULL DEFAULT 0
);
"""

bp = Blueprint("lounges", __name__, url_prefix="/lounges", template_folder="templates")

from app.modules.lounges import views  # noqa: E402,F401  ルートの登録のため
