"""会議室の予約。"""

from flask import Blueprint

TITLE = "会議室の予約"

SCHEMA = """
CREATE TABLE IF NOT EXISTS meeting_rooms_rooms (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS meeting_rooms_bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code TEXT NOT NULL REFERENCES meeting_rooms_rooms(code),
    employee_no TEXT NOT NULL,
    date TEXT NOT NULL,
    start_min INTEGER NOT NULL,
    end_min INTEGER NOT NULL,
    cancelled INTEGER NOT NULL DEFAULT 0
);
"""

bp = Blueprint("meeting_rooms", __name__, url_prefix="/meeting_rooms", template_folder="templates")

from . import views  # noqa: E402,F401
