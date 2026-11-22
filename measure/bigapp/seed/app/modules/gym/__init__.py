"""トレーニングルームの予約。"""

from app.modules.gym.web import bp

TITLE = "トレーニングルームの予約"

SCHEMA = """
CREATE TABLE IF NOT EXISTS gym_rooms (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS gym_bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code TEXT NOT NULL REFERENCES gym_rooms(code),
    employee_no TEXT NOT NULL REFERENCES employees(employee_no),
    book_date TEXT NOT NULL,
    start_min INTEGER NOT NULL,
    end_min INTEGER NOT NULL,
    cancelled INTEGER NOT NULL DEFAULT 0
);
"""

__all__ = ["bp", "TITLE", "SCHEMA"]
