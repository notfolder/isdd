"""来客用駐車場の判定と処理（総務規程 第 4 条・第 6 条・第 7 条）。"""

import datetime
import re

from app.core import audit, clock
from app.core.db import get_db
from app.modules.guest_parking import repo

# 予約の時間の単位（30 分）。開始と終了はこの倍数の時刻でなければならない。
SLOT = datetime.timedelta(minutes=30)
# 予約できる時間帯（9:00 から 18:00）
OPEN_AT = datetime.timedelta(hours=9)
CLOSE_AT = datetime.timedelta(hours=18)
# 1 人が同じ日に取れる予約の上限
MAX_PER_DAY = 2

_TIME_RE = re.compile(r"^(\d{2}):(\d{2})$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class InputError(Exception):
    """入力を受け付けない理由。メッセージを画面に出す。"""


def parse_date(text):
    text = (text or "").strip()
    if not _DATE_RE.match(text):
        raise InputError("日付は YYYY-MM-DD の形で入力してください")
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        raise InputError("日付が正しくありません")


def parse_time(text):
    """HH:MM を 0:00 からの経過時間にする。"""
    m = _TIME_RE.match((text or "").strip())
    if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
        raise InputError("時刻は HH:MM の形で入力してください")
    return datetime.timedelta(hours=int(m.group(1)), minutes=int(m.group(2)))


def format_time(delta):
    minutes = int(delta.total_seconds() // 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def create_room(code, name):
    code, name = (code or "").strip(), (name or "").strip()
    if not code:
        raise InputError("部屋の番号を入力してください")
    if not name:
        raise InputError("部屋の名前を入力してください")
    if repo.find_room(code):
        raise InputError("この部屋の番号は既に登録されています")
    repo.insert_room(code, name)
    audit.record("guest_parking", "room_create", code)
    get_db().commit()


def update_room(code, name):
    code, name = (code or "").strip(), (name or "").strip()
    if not name:
        raise InputError("部屋の名前を入力してください")
    if repo.find_room(code) is None:
        raise InputError("部屋が見つかりません")
    repo.update_room(code, name)
    audit.record("guest_parking", "room_update", code)
    get_db().commit()


def book(room_code, employee_no, date_text, start_text, end_text):
    room_code = (room_code or "").strip()
    employee_no = (employee_no or "").strip()
    if repo.find_room(room_code) is None:
        raise InputError("部屋が見つかりません")
    if repo.find_active_employee(employee_no) is None:
        raise InputError("在籍している社員ではありません")
    day = parse_date(date_text)
    start, end = parse_time(start_text), parse_time(end_text)
    if day < clock.today():
        raise InputError("過去の日付は予約できません")
    if start % SLOT or end % SLOT:
        raise InputError("時刻は 30 分単位で入力してください")
    if start < OPEN_AT or end > CLOSE_AT:
        raise InputError("予約できるのは 9:00 から 18:00 の間です")
    if start >= end:
        raise InputError("開始は終了より前にしてください")
    day_text, start_t, end_t = day.isoformat(), format_time(start), format_time(end)
    if repo.count_overlapping(room_code, day_text, start_t, end_t):
        raise InputError("その時間は既に予約があります")
    if repo.count_employee_bookings(employee_no, day_text) >= MAX_PER_DAY:
        raise InputError("1 人が 1 日に取れる予約は 2 件までです")
    booking_id = repo.insert_booking(room_code, employee_no, day_text, start_t, end_t)
    audit.record("guest_parking", "book", str(booking_id))
    get_db().commit()
    return booking_id


def cancel(booking_id_text):
    try:
        booking_id = int((booking_id_text or "").strip())
    except ValueError:
        raise InputError("予約が見つかりません")
    row = repo.find_booking(booking_id)
    if row is None or row["cancelled"]:
        raise InputError("予約が見つかりません")
    repo.cancel_booking(booking_id)
    audit.record("guest_parking", "cancel", str(booking_id))
    get_db().commit()


def status():
    return {
        "bookings": [
            {
                "id": r["id"],
                "room": r["room_code"],
                "employee": r["employee_no"],
                "date": r["day"],
                "start": r["start_time"],
                "end": r["end_time"],
            }
            for r in repo.list_bookings()
        ]
    }


def day_table(day_text):
    """その日の部屋ごとの予約。[(部屋, [予約, ...]), ...]（開始の早い順）。"""
    day = parse_date(day_text).isoformat()
    rows = repo.list_bookings(day)
    return [
        (room, sorted((r for r in rows if r["room_code"] == room["code"]), key=lambda r: r["start_time"]))
        for room in repo.list_rooms()
    ]


def list_view(date_text):
    """一覧の画面用。date が空なら全件。"""
    day = parse_date(date_text).isoformat() if (date_text or "").strip() else None
    return repo.list_rooms(), repo.list_bookings(day)
