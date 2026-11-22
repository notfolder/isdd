"""屋上スペースの予約。"""

from flask import Blueprint

TITLE = "屋上スペースの予約"

SCHEMA = """
CREATE TABLE IF NOT EXISTS rooftop_rooms (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rooftop_bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code TEXT NOT NULL REFERENCES rooftop_rooms(code),
    employee_no TEXT NOT NULL,
    date TEXT NOT NULL,
    start_min INTEGER NOT NULL,
    end_min INTEGER NOT NULL,
    cancelled INTEGER NOT NULL DEFAULT 0
);
"""

bp = Blueprint("rooftop", __name__, url_prefix="/rooftop", template_folder="templates")

from app.modules.rooftop import handlers  # noqa: E402,F401  ルートの登録のため
