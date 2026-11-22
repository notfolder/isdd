"""実験室の予約の判定。受け付けられないときは BookingError を投げる（画面側で 400 にする）。"""

import datetime

from app.core import clock
from app.core.db import get_db


class BookingError(Exception):
    """入力を受け付けない理由を持つ例外。"""


def _minutes(text, label):
    """HH:MM を 0 時からの分に直す。形が違えば BookingError。"""
    try:
        parsed = datetime.datetime.strptime(text, "%H:%M")
    except (TypeError, ValueError):
        raise BookingError(f"{label}は HH:MM の形で入力してください")
    return parsed.hour * 60 + parsed.minute


def _parse_date(text):
    try:
        return datetime.date.fromisoformat(text)
    except (TypeError, ValueError):
        raise BookingError("日付は YYYY-MM-DD の形で入力してください")


def _get_room(code):
    return get_db().execute("SELECT * FROM labs_rooms WHERE code = ?", (code,)).fetchone()


def create_room(code, name):
    """部屋を登録する。番号の重複は不可。"""
    code, name = (code or "").strip(), (name or "").strip()
    if not code:
        raise BookingError("部屋の番号を入力してください")
    if not name:
        raise BookingError("部屋の名前を入力してください")
    if _get_room(code):
        raise BookingError("この部屋の番号は既に登録されています")
    get_db().execute("INSERT INTO labs_rooms (code, name) VALUES (?, ?)", (code, name))
    return code


def update_room(code, name):
    """部屋の名前を直す。"""
    code, name = (code or "").strip(), (name or "").strip()
    if not _get_room(code):
        raise BookingError("部屋が見つかりません")
    if not name:
        raise BookingError("部屋の名前を入力してください")
    get_db().execute("UPDATE labs_rooms SET name = ? WHERE code = ?", (name, code))
    return code


def book(room_code, employee_no, date_text, start_text, end_text):
    """予約する。きまりに合わなければ BookingError。取れた予約の id を返す。"""
    conn = get_db()
    if not _get_room(room_code):
        raise BookingError("部屋が見つかりません")
    # 対象は在籍している社員だけ（退職していない社員）
    employee = conn.execute("SELECT status FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()
    if employee is None:
        raise BookingError("社員が見つかりません")
    if employee["status"] == "retired":
        raise BookingError("退職した社員は予約できません")

    day = _parse_date(date_text)
    start = _minutes(start_text, "開始")
    end = _minutes(end_text, "終了")
    # 60 分の単位。開始も終了も 60 分の倍数の時刻
    if start % 60 != 0 or end % 60 != 0:
        raise BookingError("予約は 60 分の単位で取ってください")
    # 9:00 から 18:00 の間
    if start < 9 * 60 or end > 18 * 60:
        raise BookingError("予約は 9:00 から 18:00 の間で取ってください")
    if start >= end:
        raise BookingError("開始は終了より前にしてください")
    # 今日はよいが、過去の日付はだめ
    if day < clock.today():
        raise BookingError("過去の日付は予約できません")

    day_text = day.isoformat()
    # 1 人が同じ日に取れるのは 2 件まで
    count = conn.execute(
        "SELECT COUNT(*) FROM labs_bookings WHERE employee_no = ? AND date = ? AND cancelled = 0",
        (employee_no, day_text),
    ).fetchone()[0]
    if count >= 2:
        raise BookingError("1 人が 1 日に取れる予約は 2 件までです")
    # 同じ部屋の同じ日の重なり。終了と開始が同じ時刻は重ならない
    for row in conn.execute(
        "SELECT start, \"end\" FROM labs_bookings WHERE room_code = ? AND date = ? AND cancelled = 0",
        (room_code, day_text),
    ):
        if _minutes(row["start"], "開始") < end and start < _minutes(row["end"], "終了"):
            raise BookingError("その時間は既に予約があります")

    cursor = conn.execute(
        "INSERT INTO labs_bookings (room_code, employee_no, date, start, \"end\") VALUES (?, ?, ?, ?, ?)",
        (room_code, employee_no, day_text, f"{start // 60:02d}:{start % 60:02d}", f"{end // 60:02d}:{end % 60:02d}"),
    )
    return cursor.lastrowid


def cancel(booking_id):
    """予約を取り消す。取り消し済みや存在しない予約は BookingError。"""
    conn = get_db()
    row = conn.execute("SELECT id, cancelled FROM labs_bookings WHERE id = ?", (booking_id,)).fetchone()
    if row is None or row["cancelled"]:
        raise BookingError("予約が見つかりません")
    conn.execute("UPDATE labs_bookings SET cancelled = 1 WHERE id = ?", (row["id"],))
    return row["id"]


def list_bookings(date_text=None):
    """取り消していない予約を id の昇順で返す。日付を渡せばその日だけ。"""
    sql = "SELECT * FROM labs_bookings WHERE cancelled = 0"
    args = []
    if date_text:
        sql += " AND date = ?"
        args.append(_parse_date(date_text).isoformat())
    return get_db().execute(sql + " ORDER BY id", args).fetchall()


def list_rooms():
    return get_db().execute("SELECT * FROM labs_rooms ORDER BY code").fetchall()
