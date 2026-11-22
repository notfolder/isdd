"""集中ブースの予約。部屋の登録と、30 分単位の予約を扱う。"""

from app.modules.focus_booths.web import bp

TITLE = "集中ブースの予約"

SCHEMA = """
CREATE TABLE IF NOT EXISTS focus_booths_rooms (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS focus_booths_bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code TEXT NOT NULL REFERENCES focus_booths_rooms(code),
    employee_no TEXT NOT NULL,
    date TEXT NOT NULL,
    start TEXT NOT NULL,
    "end" TEXT NOT NULL,
    cancelled INTEGER NOT NULL DEFAULT 0
);
"""

__all__ = ["bp", "TITLE", "SCHEMA"]
