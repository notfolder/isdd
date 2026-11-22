"""会議室予約の判定。総務規程 第 4 条・第 6 条にもとづく。"""

import datetime
import re

from app.core import clock

SLOT_MINUTES = 30          # 予約の時間の単位（分）
OPEN_MINUTE = 9 * 60       # 予約できる最初の時刻（9:00）
CLOSE_MINUTE = 18 * 60     # 予約できる最後の時刻（18:00）
MAX_PER_DAY = 3            # 1 人が 1 日に取れる予約の数

_TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")


def is_retired(employee) -> bool:
    """社員が退職しているか。"""
    return employee["status"] == "retired"


def parse_time(text):
    """HH:MM を 0 時からの分に直す。形式が違えば None。"""
    m = _TIME_RE.match((text or "").strip())
    if not m:
        return None
    hour, minute = int(m.group(1)), int(m.group(2))
    if hour > 23 or minute > 59:
        return None
    return hour * 60 + minute


def format_minute(minute: int) -> str:
    return f"{minute // 60:02d}:{minute % 60:02d}"


def parse_date(text):
    """YYYY-MM-DD を日付に直す。形式が違えば None。"""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", (text or "").strip()):
        return None
    try:
        return datetime.date.fromisoformat(text.strip())
    except ValueError:
        return None


class BookingRules:
    """予約を受け付けてよいかの判定。受け付けないときは理由の文を返す。"""

    def __init__(self, db):
        self.db = db

    def check_room_code(self, code, name):
        if not code:
            return "部屋の番号を入力してください"
        if not name:
            return "部屋の名前を入力してください"
        return None

    def check_booking(self, room_code, employee_no, date_text, start_text, end_text):
        """予約の入力を確かめる。問題なければ None。"""
        if self.db.execute("SELECT 1 FROM meeting_rooms_rooms WHERE code = ?", (room_code,)).fetchone() is None:
            return "部屋が見つかりません"
        employee = self.db.execute("SELECT * FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()
        if employee is None:
            return "社員が見つかりません"
        if is_retired(employee):
            return "退職した社員は予約できません"
        date = parse_date(date_text)
        if date is None:
            return "日付は YYYY-MM-DD で入力してください"
        start, end = parse_time(start_text), parse_time(end_text)
        if start is None or end is None:
            return "時刻は HH:MM で入力してください"
        if start % SLOT_MINUTES or end % SLOT_MINUTES:
            return f"時刻は {SLOT_MINUTES} 分単位で入力してください"
        if start < OPEN_MINUTE or end > CLOSE_MINUTE:
            return "予約できるのは 9:00 から 18:00 の間です"
        if start >= end:
            return "終了は開始より後にしてください"
        if date < clock.today():
            return "過去の日付は予約できません"
        iso = date.isoformat()
        overlap = self.db.execute(
            "SELECT 1 FROM meeting_rooms_bookings WHERE room_code = ? AND date = ? AND cancelled = 0 "
            "AND start_min < ? AND end_min > ?",
            (room_code, iso, end, start),
        ).fetchone()
        if overlap:
            return "その時間は既に予約されています"
        count = self.db.execute(
            "SELECT COUNT(*) FROM meeting_rooms_bookings WHERE employee_no = ? AND date = ? AND cancelled = 0",
            (employee_no, iso),
        ).fetchone()[0]
        if count >= MAX_PER_DAY:
            return f"1 日に取れる予約は {MAX_PER_DAY} 件までです"
        return None
