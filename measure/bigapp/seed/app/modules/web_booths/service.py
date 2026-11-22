"""Web 会議ブースの判定と処理。画面（routes.py）と SQL（repo.py）の間に立つ。"""

import datetime
import re

from app.core import audit, clock
from app.core.db import get_db
from app.modules.web_booths import repo

# 機能の設定。時間の単位や上限はここだけに置く。
SETTINGS = {
    "slot_minutes": 30,  # 予約の時間の単位（分）
    "open_minute": 9 * 60,  # 予約できる最初の時刻（9:00）
    "close_minute": 18 * 60,  # 予約できる最後の時刻（18:00）
    "max_per_day": 3,  # 1 人が 1 日に取れる予約の数
}

_TIME_PATTERN = re.compile(r"^(\d{2}):(\d{2})$")


class BookingError(Exception):
    """入力を受け付けないときの理由。画面にそのまま出す。"""


def is_retired(employee):
    """退職した社員なら True。"""
    return employee["status"] == "retired"


def _to_minutes(text, label):
    match = _TIME_PATTERN.match(text or "")
    if not match:
        raise BookingError(f"{label}は HH:MM の形で入力してください")
    hour, minute = int(match.group(1)), int(match.group(2))
    if hour > 23 or minute > 59:
        raise BookingError(f"{label}の時刻が正しくありません")
    return hour * 60 + minute


def _parse_date(text):
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", text or ""):
        raise BookingError("日付は YYYY-MM-DD の形で入力してください")
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        raise BookingError("日付が正しくありません")


def check_date_filter(text):
    """一覧の絞り込みの日付。空なら None。"""
    if not text:
        return None
    _parse_date(text)
    return text


def create_room(code, name):
    code, name = (code or "").strip(), (name or "").strip()
    if not code:
        raise BookingError("部屋の番号を入力してください")
    if not name:
        raise BookingError("部屋の名前を入力してください")
    if repo.find_room(code) is not None:
        raise BookingError("この部屋の番号は既に登録されています")
    repo.insert_room(code, name)
    audit.record("web_booths", "room_create", code)
    get_db().commit()


def update_room(code, name):
    code, name = (code or "").strip(), (name or "").strip()
    if repo.find_room(code) is None:
        raise BookingError("部屋が見つかりません")
    if not name:
        raise BookingError("部屋の名前を入力してください")
    repo.update_room(code, name)
    audit.record("web_booths", "room_update", code)
    get_db().commit()


def book(room_code, employee_no, date_text, start_text, end_text):
    room_code, employee_no = (room_code or "").strip(), (employee_no or "").strip()
    if repo.find_room(room_code) is None:
        raise BookingError("部屋が見つかりません")
    employee = repo.find_employee(employee_no)
    if not (employee is not None and not is_retired(employee)):
        raise BookingError("在籍している社員を指定してください")

    day = _parse_date(date_text)
    if day < clock.today():
        raise BookingError("過去の日付は予約できません")

    start = _to_minutes(start_text, "開始")
    end = _to_minutes(end_text, "終了")
    slot = SETTINGS["slot_minutes"]
    if start % slot or end % slot:
        raise BookingError(f"時刻は {slot} 分の単位で入力してください")
    if start < SETTINGS["open_minute"] or end > SETTINGS["close_minute"]:
        raise BookingError("予約できるのは 9:00 から 18:00 の間です")
    if not start < end:
        raise BookingError("開始は終了より前にしてください")

    if repo.count_by_employee_on(employee_no, date_text) >= SETTINGS["max_per_day"]:
        raise BookingError(f"1 日に取れる予約は {SETTINGS['max_per_day']} 件までです")
    if repo.count_overlapping(room_code, date_text, start_text, end_text) > 0:
        raise BookingError("同じ部屋の同じ時間に、既に予約があります")

    repo.insert_booking(room_code, employee_no, date_text, start_text, end_text)
    audit.record("web_booths", "book", f"{room_code} {employee_no} {date_text} {start_text}-{end_text}")
    get_db().commit()


def cancel(booking_id):
    try:
        number = int(booking_id)
    except (TypeError, ValueError):
        raise BookingError("予約が見つかりません")
    booking = repo.find_booking(number)
    if booking is None or booking["cancelled"]:
        raise BookingError("予約が見つかりません")
    repo.cancel_booking(number)
    audit.record("web_booths", "cancel", str(number))
    get_db().commit()


def status():
    return {
        "bookings": [
            {
                "id": b["id"],
                "room": b["room_code"],
                "employee": b["employee_no"],
                "date": b["date"],
                "start": b["start"],
                "end": b["end"],
            }
            for b in repo.list_bookings_by_id()
        ]
    }
