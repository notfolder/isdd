"""応接室の予約。部屋の登録と、30 分単位の予約・取消を扱う。"""

from flask import Blueprint

TITLE = "応接室の予約"

SCHEMA = """
CREATE TABLE IF NOT EXISTS reception_rooms_rooms (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reception_rooms_bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code TEXT NOT NULL REFERENCES reception_rooms_rooms(code),
    employee_no TEXT NOT NULL,
    date TEXT NOT NULL,
    start TEXT NOT NULL,
    end TEXT NOT NULL,
    cancelled INTEGER NOT NULL DEFAULT 0
);
"""

bp = Blueprint("reception_rooms", __name__, url_prefix="/reception_rooms", template_folder="templates")

from app.modules.reception_rooms import handlers  # noqa: E402,F401  ルートの登録のために読み込む
