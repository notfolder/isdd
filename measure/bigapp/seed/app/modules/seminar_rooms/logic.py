"""研修室の予約の処理。画面（__init__.py）から呼ばれる。"""

import datetime
import re
from dataclasses import dataclass
from typing import Optional

from app.core import clock
from app.core.db import get_db

# 在籍していない状態（総務規程 第 6 条）
EXCLUDED_STATUSES = {"retired"}

_TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")


@dataclass
class Room:
    code: str
    name: str


@dataclass
class Booking:
    id: int
    room_code: str
    employee_no: str
    date: str
    start: str
    end: str


class InputError(Exception):
    """入力を受け付けないとき。メッセージが画面に出る理由になる。"""


def _booking(row) -> Booking:
    return Booking(row["id"], row["room_code"], row["employee_no"], row["date"], row["start"], row["end"])


def list_rooms() -> list:
    rows = get_db().execute("SELECT code, name FROM seminar_rooms_room ORDER BY code").fetchall()
    return [Room(r["code"], r["name"]) for r in rows]


def parse_date(text: str) -> datetime.date:
    """YYYY-MM-DD の日付を読む。形が違えば InputError。"""
    text = (text or "").strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        raise InputError("日付は YYYY-MM-DD の形で入力してください")
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        raise InputError("日付が正しくありません")


def parse_minutes(text: str) -> int:
    """HH:MM を 0 時からの分に直す。形が違えば InputError。"""
    text = (text or "").strip()
    if not _TIME_PATTERN.match(text):
        raise InputError("時刻は HH:MM の形で入力してください")
    hour, minute = int(text[:2]), int(text[3:])
    if hour > 23 or minute > 59:
        raise InputError("時刻が正しくありません")
    return hour * 60 + minute


def create_room(code: str, name: str) -> Room:
    code, name = (code or "").strip(), (name or "").strip()
    if not code:
        raise InputError("部屋の番号を入力してください")
    if not name:
        raise InputError("部屋の名前を入力してください")
    conn = get_db()
    if conn.execute("SELECT 1 FROM seminar_rooms_room WHERE code = ?", (code,)).fetchone():
        raise InputError("この部屋の番号は既に登録されています")
    conn.execute("INSERT INTO seminar_rooms_room (code, name) VALUES (?, ?)", (code, name))
    return Room(code, name)


def update_room(code: str, name: str) -> Room:
    code, name = (code or "").strip(), (name or "").strip()
    if not name:
        raise InputError("部屋の名前を入力してください")
    conn = get_db()
    if conn.execute("SELECT 1 FROM seminar_rooms_room WHERE code = ?", (code,)).fetchone() is None:
        raise InputError("部屋が見つかりません")
    conn.execute("UPDATE seminar_rooms_room SET name = ? WHERE code = ?", (name, code))
    return Room(code, name)


def create_booking(room_code: str, employee_no: str, date_text: str, start_text: str, end_text: str) -> Booking:
    """予約を 1 件取る。きまりに合わなければ InputError。"""
    room_code, employee_no = (room_code or "").strip(), (employee_no or "").strip()
    conn = get_db()
    if conn.execute("SELECT 1 FROM seminar_rooms_room WHERE code = ?", (room_code,)).fetchone() is None:
        raise InputError("部屋が見つかりません")
    employee = conn.execute("SELECT status FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()
    if employee is None:
        raise InputError("社員が見つかりません")
    if employee["status"] in EXCLUDED_STATUSES:
        raise InputError("退職した社員は予約できません")

    day = parse_date(date_text)
    start, end = parse_minutes(start_text), parse_minutes(end_text)
    # 60 分の単位（開始も終了も 60 分の倍数）
    if start % 60 != 0 or end % 60 != 0:
        raise InputError("予約は 60 分の単位で、ちょうどの時刻に取ってください")
    if start < 9 * 60 or end > 18 * 60:
        raise InputError("予約は 9:00 から 18:00 の間に取ってください")
    if start >= end:
        raise InputError("終了は開始より後にしてください")
    if day < clock.today():
        raise InputError("過去の日付は予約できません")

    date_iso = day.isoformat()
    # 同じ部屋の同じ日に、時間が重なる予約（終了と開始が同じ時刻は重ならない）
    for row in conn.execute(
        "SELECT start, end FROM seminar_rooms_booking WHERE room_code = ? AND date = ? AND cancelled = 0",
        (room_code, date_iso),
    ).fetchall():
        if start < parse_minutes(row["end"]) and parse_minutes(row["start"]) < end:
            raise InputError("その時間は既に予約されています")
    # 1 人が同じ日に取れるのは 1 件まで
    if conn.execute(
        "SELECT 1 FROM seminar_rooms_booking WHERE employee_no = ? AND date = ? AND cancelled = 0",
        (employee_no, date_iso),
    ).fetchone():
        raise InputError("この社員は同じ日に既に予約があります（1 日 1 件まで）")

    start_text, end_text = "%02d:%02d" % (start // 60, start % 60), "%02d:%02d" % (end // 60, end % 60)
    cursor = conn.execute(
        "INSERT INTO seminar_rooms_booking (room_code, employee_no, date, start, end, cancelled) VALUES (?, ?, ?, ?, ?, 0)",
        (room_code, employee_no, date_iso, start_text, end_text),
    )
    return Booking(cursor.lastrowid, room_code, employee_no, date_iso, start_text, end_text)


def cancel_booking(booking_id_text: str) -> Booking:
    conn = get_db()
    try:
        booking_id = int((booking_id_text or "").strip())
    except ValueError:
        raise InputError("予約の番号が正しくありません")
    row = conn.execute("SELECT * FROM seminar_rooms_booking WHERE id = ? AND cancelled = 0", (booking_id,)).fetchone()
    if row is None:
        raise InputError("予約が見つかりません")
    conn.execute("UPDATE seminar_rooms_booking SET cancelled = 1 WHERE id = ?", (booking_id,))
    return _booking(row)


def list_bookings(date_iso: Optional[str] = None) -> list:
    """取り消していない予約。日付を指定すればその日だけ。"""
    sql = "SELECT * FROM seminar_rooms_booking WHERE cancelled = 0"
    params = ()
    if date_iso:
        sql += " AND date = ?"
        params = (date_iso,)
    rows = get_db().execute(sql + " ORDER BY date, start, id", params).fetchall()
    return [_booking(r) for r in rows]


def list_bookings_by_id() -> list:
    rows = get_db().execute("SELECT * FROM seminar_rooms_booking WHERE cancelled = 0 ORDER BY id").fetchall()
    return [_booking(r) for r in rows]
