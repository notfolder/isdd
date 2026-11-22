"""Web 会議ブースの予約。部屋の登録と、30 分単位の予約・取消を扱う。"""

from app.modules.web_booths.routes import bp

TITLE = "Web 会議ブースの予約"

SCHEMA = """
CREATE TABLE IF NOT EXISTS web_booths_rooms (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS web_booths_bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code TEXT NOT NULL REFERENCES web_booths_rooms(code),
    employee_no TEXT NOT NULL,
    date TEXT NOT NULL,
    start TEXT NOT NULL,
    end TEXT NOT NULL,
    cancelled INTEGER NOT NULL DEFAULT 0
);
"""

__all__ = ["bp", "TITLE", "SCHEMA"]
