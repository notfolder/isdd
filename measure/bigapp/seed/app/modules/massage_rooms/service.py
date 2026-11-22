"""判定と処理の層。きまりに合わないときは RuleError を投げる。"""

import datetime
import re

from app.core import audit, clock

from . import repo

# 機能の設定。時間の単位などはここだけで決める。
SETTINGS = {
    "slot_minutes": 30,  # 予約の単位（分）
    "open_minute": 9 * 60,  # 9:00
    "close_minute": 18 * 60,  # 18:00
    "max_per_day": 1,  # 1 人が 1 日に取れる予約の数
}

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")


class RuleError(Exception):
    """入力を受け付けない理由（画面にそのまま出す）。"""


def is_retired(employee):
    """退職した社員か。"""
    return employee["status"] == "retired"


def parse_date(text):
    text = (text or "").strip()
    if not _DATE_RE.match(text):
        raise RuleError("日付は YYYY-MM-DD で入力してください")
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        raise RuleError("日付が正しくありません")


def parse_time(text):
    """HH:MM を 0 時からの分に直す。"""
    text = (text or "").strip()
    if not _TIME_RE.match(text):
        raise RuleError("時刻は HH:MM で入力してください")
    hour, minute = int(text[:-3]), int(text[-2:])
    if hour > 24 or minute > 59:
        raise RuleError("時刻が正しくありません")
    return hour * 60 + minute


def format_time(minutes):
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _need(value, label):
    value = (value or "").strip()
    if not value:
        raise RuleError(f"{label}を入力してください")
    return value


def create_room(code, name):
    code, name = _need(code, "部屋の番号"), _need(name, "部屋の名前")
    if repo.get_room(code) is not None:
        raise RuleError("この部屋の番号は既に登録されています")
    repo.insert_room(code, name)
    audit.record("massage_rooms", "room_create", code)
    repo.commit()


def update_room(code, name):
    code, name = _need(code, "部屋の番号"), _need(name, "部屋の名前")
    if repo.get_room(code) is None:
        raise RuleError("部屋が見つかりません")
    repo.update_room(code, name)
    audit.record("massage_rooms", "room_update", code)
    repo.commit()


def book(room_code, employee_no, date_text, start_text, end_text):
    room_code = (room_code or "").strip()
    employee_no = (employee_no or "").strip()
    if repo.get_room(room_code) is None:
        raise RuleError("部屋が見つかりません")
    employee = repo.get_employee(employee_no)
    if employee is None:
        raise RuleError("社員が見つかりません")
    if is_retired(employee):
        raise RuleError("退職した社員は予約できません")
    date = parse_date(date_text)
    start, end = parse_time(start_text), parse_time(end_text)
    unit = SETTINGS["slot_minutes"]
    if start % unit or end % unit:
        raise RuleError(f"予約は {unit} 分単位で入力してください")
    if start < SETTINGS["open_minute"] or end > SETTINGS["close_minute"]:
        raise RuleError(f"予約は {format_time(SETTINGS['open_minute'])} から {format_time(SETTINGS['close_minute'])} の間です")
    if start >= end:
        raise RuleError("終了は開始より後にしてください")
    if date < clock.today():
        raise RuleError("過去の日付は予約できません")
    iso = date.isoformat()
    for other in repo.list_room_bookings(room_code, iso):
        if start < other["end_min"] and other["start_min"] < end:
            raise RuleError("その時間は既に予約されています")
    if repo.count_employee_bookings(employee_no, iso) >= SETTINGS["max_per_day"]:
        raise RuleError("1 人が 1 日に取れる予約の数を超えています")
    repo.insert_booking(room_code, employee_no, iso, start, end)
    audit.record("massage_rooms", "book", f"{room_code} {employee_no} {iso} {format_time(start)}-{format_time(end)}")
    repo.commit()


def cancel(booking_id_text):
    try:
        booking_id = int((booking_id_text or "").strip())
    except ValueError:
        raise RuleError("予約の番号が正しくありません")
    booking = repo.get_booking(booking_id)
    if booking is None or booking["cancelled"]:
        raise RuleError("予約が見つかりません")
    repo.cancel_booking(booking_id)
    audit.record("massage_rooms", "cancel", str(booking_id))
    repo.commit()


def _view(row):
    return {
        "id": row["id"],
        "room": row["room_code"],
        "employee": row["employee_no"],
        "date": row["date"],
        "start": format_time(row["start_min"]),
        "end": format_time(row["end_min"]),
    }


def bookings(date_text=None):
    """一覧用の予約。date_text があればその日だけ（形が正しくなければ RuleError）。"""
    date = None
    if date_text:
        date = parse_date(date_text).isoformat()
    return [_view(r) for r in repo.list_bookings(date)]


def rooms():
    return repo.list_rooms()


def day_table(date_text):
    """部屋ごとの、その日の予約。"""
    iso = parse_date(date_text).isoformat()
    result = []
    for room in repo.list_rooms():
        items = [_view(r) for r in repo.list_room_bookings(room["code"], iso)]
        items.sort(key=lambda v: v["start"])
        result.append({"room": room, "bookings": items})
    return iso, result
