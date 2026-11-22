"""マッサージ室の予約。部屋の登録と、30 分単位の予約を扱う。"""

from flask import Blueprint

TITLE = "マッサージ室の予約"

SCHEMA = """
CREATE TABLE IF NOT EXISTS massage_rooms_room (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS massage_rooms_booking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code TEXT NOT NULL REFERENCES massage_rooms_room(code),
    employee_no TEXT NOT NULL,
    date TEXT NOT NULL,
    start_min INTEGER NOT NULL,
    end_min INTEGER NOT NULL,
    cancelled INTEGER NOT NULL DEFAULT 0
);
"""

bp = Blueprint("massage_rooms", __name__, url_prefix="/massage_rooms", template_folder="templates")

from . import routes  # noqa: E402,F401  ルートを登録するために読み込む
