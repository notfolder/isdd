"""来客用駐車場の予約。部屋（区画）の登録と、30 分単位の予約を扱う。"""

from app.modules.guest_parking.routes import bp

TITLE = "来客用駐車場の予約"

SCHEMA = """
CREATE TABLE IF NOT EXISTS guest_parking_rooms (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS guest_parking_bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code TEXT NOT NULL REFERENCES guest_parking_rooms(code),
    employee_no TEXT NOT NULL,
    day TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    cancelled INTEGER NOT NULL DEFAULT 0
);
"""

__all__ = ["bp", "TITLE", "SCHEMA"]
