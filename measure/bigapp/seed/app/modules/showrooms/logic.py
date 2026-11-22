"""ショールーム予約の処理。部屋の登録と、予約の判定・登録・取消を行う。"""

import datetime
import re
from dataclasses import dataclass

from app.core import clock
from app.core.db import get_db

UNIT = 30  # 予約の時間の単位（分）
OPEN_MINUTES = 9 * 60  # 予約できる最初の時刻（9:00）
CLOSE_MINUTES = 18 * 60  # 予約できる最後の時刻（18:00）
DAILY_LIMIT = 2  # 1 人が 1 日に取れる予約の数

_TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")


class InputError(Exception):
    """入力を受け付けないときの理由（画面にそのまま出す）。"""


@dataclass
class Room:
    code: str
    name: str


@dataclass
class Booking:
    id: int
    room: str
    employee: str
    date: str
    start: str
    end: str


def to_minutes(text: str) -> int:
    """HH:MM を 0 時からの分に直す。形式が違えば InputError。"""
    m = _TIME_RE.match((text or "").strip())
    if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
        raise InputError("時刻は HH:MM の形式で入力してください")
    return int(m.group(1)) * 60 + int(m.group(2))


def to_text(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def parse_date(text: str) -> datetime.date:
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", (text or "").strip()):
            raise ValueError
        return datetime.date.fromisoformat(text.strip())
    except ValueError:
        raise InputError("日付は YYYY-MM-DD の形式で入力してください")


def list_rooms() -> list:
    rows = get_db().execute("SELECT code, name FROM showrooms_rooms ORDER BY code").fetchall()
    return [Room(r["code"], r["name"]) for r in rows]


def list_bookings(date: str = None) -> list:
    """取り消していない予約を、日付と開始の順で返す。date があればその日だけ。"""
    sql = "SELECT * FROM showrooms_bookings WHERE cancelled = 0"
    args = []
    if date:
        sql += " AND date = ?"
        args.append(date)
    rows = get_db().execute(sql + " ORDER BY date, start_min, id", args).fetchall()
    return [_booking(r) for r in rows]


def status_bookings() -> list:
    """status.json 用。取り消していない予約を id の昇順で返す。"""
    rows = get_db().execute("SELECT * FROM showrooms_bookings WHERE cancelled = 0 ORDER BY id").fetchall()
    return [_booking(r) for r in rows]


def _booking(r) -> Booking:
    return Booking(r["id"], r["room_code"], r["employee_no"], r["date"], to_text(r["start_min"]), to_text(r["end_min"]))


def create_room(code: str, name: str) -> str:
    code, name = (code or "").strip(), (name or "").strip()
    if not code:
        raise InputError("部屋の番号を入力してください")
    if not name:
        raise InputError("部屋の名前を入力してください")
    conn = get_db()
    if conn.execute("SELECT 1 FROM showrooms_rooms WHERE code = ?", (code,)).fetchone():
        raise InputError("この部屋の番号は既に登録されています")
    conn.execute("INSERT INTO showrooms_rooms (code, name) VALUES (?, ?)", (code, name))
    return code


def update_room(code: str, name: str) -> str:
    code, name = (code or "").strip(), (name or "").strip()
    if not name:
        raise InputError("部屋の名前を入力してください")
    conn = get_db()
    if conn.execute("SELECT 1 FROM showrooms_rooms WHERE code = ?", (code,)).fetchone() is None:
        raise InputError("部屋が見つかりません")
    conn.execute("UPDATE showrooms_rooms SET name = ? WHERE code = ?", (name, code))
    return code


def book(room_code: str, employee_no: str, date_text: str, start_text: str, end_text: str) -> str:
    """予約を登録する。きまりに合わなければ InputError。登録した予約の説明を返す。"""
    conn = get_db()
    room_code, employee_no = (room_code or "").strip(), (employee_no or "").strip()
    if conn.execute("SELECT 1 FROM showrooms_rooms WHERE code = ?", (room_code,)).fetchone() is None:
        raise InputError("部屋が見つかりません")
    emp = conn.execute("SELECT status FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()
    if emp is None:
        raise InputError("社員が見つかりません")
    if emp["status"] != "active":
        raise InputError("退職した社員は予約できません")

    date = parse_date(date_text)
    start, end = to_minutes(start_text), to_minutes(end_text)
    if start % UNIT != 0 or end % UNIT != 0:
        raise InputError(f"時刻は {UNIT} 分の単位で入力してください")
    if start < OPEN_MINUTES or end > CLOSE_MINUTES:
        raise InputError("予約は 9:00 から 18:00 の間で取ってください")
    if start >= end:
        raise InputError("終了は開始より後にしてください")
    if date < clock.today():
        raise InputError("過去の日付は予約できません")

    day = date.isoformat()
    # 前の予約の終了と次の開始が同じ時刻なのは重なりではない
    clash = conn.execute(
        "SELECT 1 FROM showrooms_bookings WHERE cancelled = 0 AND room_code = ? AND date = ? AND start_min < ? AND end_min > ?",
        (room_code, day, end, start),
    ).fetchone()
    if clash:
        raise InputError("その時間は既に予約があります")
    count = conn.execute(
        "SELECT COUNT(*) FROM showrooms_bookings WHERE cancelled = 0 AND employee_no = ? AND date = ?", (employee_no, day)
    ).fetchone()[0]
    if count >= DAILY_LIMIT:
        raise InputError(f"1 日に取れる予約は {DAILY_LIMIT} 件までです")
    cur = conn.execute(
        "INSERT INTO showrooms_bookings (room_code, employee_no, date, start_min, end_min) VALUES (?, ?, ?, ?, ?)",
        (room_code, employee_no, day, start, end),
    )
    return str(cur.lastrowid)


def cancel(booking_id: str) -> str:
    conn = get_db()
    try:
        number = int(booking_id)
    except (TypeError, ValueError):
        raise InputError("予約が見つかりません")
    row = conn.execute("SELECT cancelled FROM showrooms_bookings WHERE id = ?", (number,)).fetchone()
    if row is None:
        raise InputError("予約が見つかりません")
    if row["cancelled"]:
        raise InputError("この予約は既に取り消されています")
    conn.execute("UPDATE showrooms_bookings SET cancelled = 1 WHERE id = ?", (number,))
    return str(number)
