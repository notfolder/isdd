"""予約の判定。受け付けないときは GymError を投げる（画面側で受けて 400 にする）。"""

import datetime
import re

from app.core import clock
from app.core.db import get_db


class GymError(Exception):
    """入力を受け付けないときの例外。メッセージは画面に出す理由。"""


def parse_date(text):
    """YYYY-MM-DD の文字列を日付にする。"""
    text = (text or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        raise GymError("日付は YYYY-MM-DD の形で入力してください")
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        raise GymError("日付が正しくありません")


def parse_time(text, label):
    """HH:MM の文字列を 0 時からの分にする。"""
    text = (text or "").strip()
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", text)
    if not m:
        raise GymError(f"{label}は HH:MM の形で入力してください")
    hour, minute = int(m.group(1)), int(m.group(2))
    if hour > 23 or minute > 59:
        raise GymError(f"{label}が正しくありません")
    return hour * 60 + minute


def format_time(minutes):
    """分を HH:MM の文字列にする。"""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def create_room(code, name):
    code, name = (code or "").strip(), (name or "").strip()
    if not code:
        raise GymError("部屋の番号を入力してください")
    if not name:
        raise GymError("部屋の名前を入力してください")
    conn = get_db()
    if conn.execute("SELECT 1 FROM gym_rooms WHERE code = ?", (code,)).fetchone():
        raise GymError("この部屋の番号は既に登録されています")
    conn.execute("INSERT INTO gym_rooms (code, name) VALUES (?, ?)", (code, name))
    return code


def update_room(code, name):
    code, name = (code or "").strip(), (name or "").strip()
    conn = get_db()
    if conn.execute("SELECT 1 FROM gym_rooms WHERE code = ?", (code,)).fetchone() is None:
        raise GymError("部屋が見つかりません")
    if not name:
        raise GymError("部屋の名前を入力してください")
    conn.execute("UPDATE gym_rooms SET name = ? WHERE code = ?", (name, code))
    return code


def book(room_code, employee_no, date_text, start_text, end_text):
    """予約を取る。作った予約の id を返す。"""
    conn = get_db()
    room_code = (room_code or "").strip()
    employee_no = (employee_no or "").strip()
    if conn.execute("SELECT 1 FROM gym_rooms WHERE code = ?", (room_code,)).fetchone() is None:
        raise GymError("部屋が見つかりません")
    # 在籍している社員だけが対象（退職していない社員）
    emp = conn.execute("SELECT status FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()
    if emp is None:
        raise GymError("社員が見つかりません")
    if emp["status"] == "retired":
        raise GymError("退職した社員は予約できません")
    day = parse_date(date_text)
    start = parse_time(start_text, "開始")
    end = parse_time(end_text, "終了")
    # 30 分単位、9:00 から 18:00 の間
    if start % 30 != 0 or end % 30 != 0:
        raise GymError("時刻は 30 分単位で入力してください")
    if start < 9 * 60 or end > 18 * 60:
        raise GymError("予約は 9:00 から 18:00 の間で取ってください")
    if not start < end:
        raise GymError("終了は開始より後にしてください")
    if day < clock.today():
        raise GymError("過去の日付は予約できません")
    iso = day.isoformat()
    # 同じ部屋の同じ日に時間が重なる予約（接するだけは重ならない）
    clash = conn.execute(
        "SELECT 1 FROM gym_bookings WHERE room_code = ? AND book_date = ? AND cancelled = 0 AND start_min < ? AND end_min > ?",
        (room_code, iso, end, start),
    ).fetchone()
    if clash:
        raise GymError("その時間は既に予約があります")
    # 1 人が同じ日に取れる予約は 1 件まで
    count = conn.execute(
        "SELECT COUNT(*) FROM gym_bookings WHERE employee_no = ? AND book_date = ? AND cancelled = 0", (employee_no, iso)
    ).fetchone()[0]
    if count >= 1:
        raise GymError("1 人が 1 日に取れる予約は 1 件までです")
    cur = conn.execute(
        "INSERT INTO gym_bookings (room_code, employee_no, book_date, start_min, end_min) VALUES (?, ?, ?, ?, ?)",
        (room_code, employee_no, iso, start, end),
    )
    return cur.lastrowid


def cancel(booking_id):
    """予約を取り消す。"""
    conn = get_db()
    try:
        bid = int((booking_id or "").strip())
    except ValueError:
        raise GymError("予約が見つかりません")
    row = conn.execute("SELECT cancelled FROM gym_bookings WHERE id = ?", (bid,)).fetchone()
    if row is None:
        raise GymError("予約が見つかりません")
    if row["cancelled"]:
        raise GymError("この予約は既に取り消されています")
    conn.execute("UPDATE gym_bookings SET cancelled = 1 WHERE id = ?", (bid,))
    return bid


def list_bookings(date_text=None):
    """取り消していない予約を id の昇順で返す。日付を渡すとその日だけ。"""
    sql = (
        "SELECT b.id, b.room_code, b.employee_no, b.book_date, b.start_min, b.end_min, "
        "e.name AS employee_name, r.name AS room_name "
        "FROM gym_bookings b JOIN gym_rooms r ON r.code = b.room_code "
        "JOIN employees e ON e.employee_no = b.employee_no WHERE b.cancelled = 0"
    )
    args = []
    if date_text:
        sql += " AND b.book_date = ?"
        args.append(parse_date(date_text).isoformat())
    sql += " ORDER BY b.id"
    return [
        {
            "id": r["id"], "room": r["room_code"], "room_name": r["room_name"], "employee": r["employee_no"],
            "employee_name": r["employee_name"], "date": r["book_date"],
            "start": format_time(r["start_min"]), "end": format_time(r["end_min"]),
        }
        for r in get_db().execute(sql, args).fetchall()
    ]


def list_rooms():
    return get_db().execute("SELECT code, name FROM gym_rooms ORDER BY code").fetchall()
