"""集中ブース予約の判定。受け付けないときは BookingError を投げ、画面側で 400 にする。"""

import datetime

from app.core import clock
from app.core.db import get_db

# 予約は 30 分単位、9:00 から 18:00 の間（総務規程 第 4 条）
ALLOWED_STARTS = tuple(f"{h:02d}:{m:02d}" for h in range(9, 18) for m in (0, 30))
ALLOWED_ENDS = tuple(f"{h:02d}:{m:02d}" for h in range(9, 19) for m in (0, 30) if "09:00" < f"{h:02d}:{m:02d}" <= "18:00")
DAILY_LIMIT = 4  # 1 人が 1 日に取れる予約の数


class BookingError(Exception):
    """入力を受け付けない理由を持つ例外。"""


def _room_exists(code):
    return get_db().execute("SELECT 1 FROM focus_booths_rooms WHERE code = ?", (code,)).fetchone() is not None


def create_room(code, name):
    """部屋を登録する。番号の重複は不可。"""
    code, name = (code or "").strip(), (name or "").strip()
    if not code:
        raise BookingError("部屋の番号を入力してください")
    if not name:
        raise BookingError("部屋の名前を入力してください")
    if _room_exists(code):
        raise BookingError("この部屋の番号は既に登録されています")
    get_db().execute("INSERT INTO focus_booths_rooms (code, name) VALUES (?, ?)", (code, name))
    return code


def update_room(code, name):
    """部屋の名前を直す。"""
    code, name = (code or "").strip(), (name or "").strip()
    if not _room_exists(code):
        raise BookingError("部屋が見つかりません")
    if not name:
        raise BookingError("部屋の名前を入力してください")
    get_db().execute("UPDATE focus_booths_rooms SET name = ? WHERE code = ?", (name, code))
    return code


def parse_date(text):
    """YYYY-MM-DD の日付を読む。"""
    text = (text or "").strip()
    try:
        if len(text) != 10:
            raise ValueError
        return datetime.date.fromisoformat(text)
    except ValueError:
        raise BookingError("日付は YYYY-MM-DD の形で入力してください")


def create_booking(room_code, employee_no, date_text, start, end):
    """予約を 1 件取る。きまりに合わなければ BookingError。取れた予約の id を返す。"""
    room_code = (room_code or "").strip()
    employee_no = (employee_no or "").strip()
    start, end = (start or "").strip(), (end or "").strip()
    db = get_db()
    if not _room_exists(room_code):
        raise BookingError("部屋が見つかりません")
    employee = db.execute("SELECT status FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()
    if employee is None:
        raise BookingError("社員が見つかりません")
    if employee["status"] != "active":
        raise BookingError("退職した社員は予約できません")
    date = parse_date(date_text)
    if date < clock.today():
        raise BookingError("過去の日付は予約できません")
    if start not in ALLOWED_STARTS:
        raise BookingError("開始は 9:00 から 17:30 の 30 分単位で入力してください")
    if end not in ALLOWED_ENDS:
        raise BookingError("終了は 9:30 から 18:00 の 30 分単位で入力してください")
    if start >= end:
        raise BookingError("開始は終了より前にしてください")
    day = date.isoformat()
    # 終了と開始が同じ時刻なのは重なりではない
    clash = db.execute(
        "SELECT 1 FROM focus_booths_bookings WHERE room_code = ? AND date = ? AND cancelled = 0 AND start < ? AND \"end\" > ?",
        (room_code, day, end, start),
    ).fetchone()
    if clash:
        raise BookingError("その時間は既に予約されています")
    count = db.execute(
        "SELECT COUNT(*) FROM focus_booths_bookings WHERE employee_no = ? AND date = ? AND cancelled = 0", (employee_no, day)
    ).fetchone()[0]
    if count >= DAILY_LIMIT:
        raise BookingError(f"1 人が 1 日に取れる予約は {DAILY_LIMIT} 件までです")
    cur = db.execute(
        "INSERT INTO focus_booths_bookings (room_code, employee_no, date, start, \"end\") VALUES (?, ?, ?, ?, ?)",
        (room_code, employee_no, day, start, end),
    )
    return cur.lastrowid


def cancel_booking(booking_id):
    """予約を取り消す。存在しない予約と取消済みの予約は受け付けない。"""
    try:
        number = int((booking_id or "").strip())
    except ValueError:
        raise BookingError("予約が見つかりません")
    db = get_db()
    row = db.execute("SELECT cancelled FROM focus_booths_bookings WHERE id = ?", (number,)).fetchone()
    if row is None:
        raise BookingError("予約が見つかりません")
    if row["cancelled"]:
        raise BookingError("この予約は既に取り消されています")
    db.execute("UPDATE focus_booths_bookings SET cancelled = 1 WHERE id = ?", (number,))
    return number


def list_rooms():
    return get_db().execute("SELECT code, name FROM focus_booths_rooms ORDER BY code").fetchall()


def list_bookings(date_text=None):
    """取り消していない予約を id の昇順で返す。日付を渡すとその日だけ。"""
    sql = (
        "SELECT b.id, b.room_code, r.name AS room_name, b.employee_no, e.name AS employee_name, b.date, b.start, b.\"end\" "
        "FROM focus_booths_bookings b JOIN focus_booths_rooms r ON r.code = b.room_code "
        "LEFT JOIN employees e ON e.employee_no = b.employee_no WHERE b.cancelled = 0"
    )
    args = ()
    if date_text:
        sql += " AND b.date = ?"
        args = (date_text,)
    return get_db().execute(sql + " ORDER BY b.id", args).fetchall()
