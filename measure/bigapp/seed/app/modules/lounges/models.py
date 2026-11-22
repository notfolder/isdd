"""ラウンジ予約の判定をまとめたクラス。"""

import datetime

from app.core import clock
from app.core.db import get_db

# 予約の時間の単位（開始も終了もこの倍数の時刻）
SLOT = datetime.timedelta(minutes=60)
OPEN_TIME = datetime.timedelta(hours=9)
CLOSE_TIME = datetime.timedelta(hours=18)
MAX_PER_PERSON_PER_DAY = 1


class BookingError(Exception):
    """受け付けられない理由。メッセージは画面にそのまま出す。"""


def parse_time(text):
    """HH:MM を 0:00 からの経過時間（timedelta）にする。形式が違えば BookingError。"""
    try:
        parsed = datetime.datetime.strptime((text or "").strip(), "%H:%M")
    except ValueError:
        raise BookingError("時刻は HH:MM の形式で入力してください")
    return datetime.timedelta(hours=parsed.hour, minutes=parsed.minute)


def format_time(delta):
    minutes = int(delta.total_seconds() // 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def parse_date(text):
    try:
        return datetime.date.fromisoformat((text or "").strip())
    except ValueError:
        raise BookingError("日付は YYYY-MM-DD の形式で入力してください")


class LoungeRules:
    """部屋の登録と予約の受け付け判定。データの変更は行わず、判定と検索だけを持つ。"""

    def __init__(self, db=None):
        self.db = db or get_db()

    # --- 部屋 ---
    def room(self, code):
        return self.db.execute("SELECT * FROM lounges_rooms WHERE code = ?", (code,)).fetchone()

    def check_new_room(self, code, name):
        if not code:
            raise BookingError("部屋の番号を入力してください")
        if not name:
            raise BookingError("部屋の名前を入力してください")
        if self.room(code) is not None:
            raise BookingError("この部屋の番号は既に登録されています")

    def check_room_update(self, code, name):
        if self.room(code) is None:
            raise BookingError("部屋が見つかりません")
        if not name:
            raise BookingError("部屋の名前を入力してください")

    # --- 社員 ---
    def check_active_employee(self, employee_no):
        """在籍している社員だけを対象にする（退職者・存在しない番号は不可）。"""
        row = self.db.execute(
            "SELECT employee_no FROM employees WHERE employee_no = ? AND status = 'active'", (employee_no,)
        ).fetchone()
        if row is None:
            raise BookingError("在籍している社員ではありません")

    # --- 予約 ---
    def check_booking(self, room_code, employee_no, date_text, start_text, end_text):
        """予約を受け付けられるか判定する。受け付けられるなら (date, start, end) の文字列を返す。"""
        if self.room(room_code) is None:
            raise BookingError("部屋が見つかりません")
        self.check_active_employee(employee_no)
        date = parse_date(date_text)
        start, end = parse_time(start_text), parse_time(end_text)
        if date < clock.today():
            raise BookingError("過去の日付は予約できません")
        if start < OPEN_TIME or end > CLOSE_TIME:
            raise BookingError("予約は 9:00 から 18:00 の間で取ってください")
        if start >= end:
            raise BookingError("終了は開始より後にしてください")
        if start % SLOT or end % SLOT:
            raise BookingError("予約は 60 分の単位で取ってください")
        date_str, start_str, end_str = date.isoformat(), format_time(start), format_time(end)
        if self._overlaps(room_code, date_str, start, end):
            raise BookingError("同じ部屋のその時間は既に予約されています")
        if self._count_for_day(employee_no, date_str) >= MAX_PER_PERSON_PER_DAY:
            raise BookingError("1 人が 1 日に取れる予約は 1 件までです")
        return date_str, start_str, end_str

    def _overlaps(self, room_code, date_str, start, end):
        rows = self.db.execute(
            "SELECT start, end FROM lounges_bookings WHERE room_code = ? AND date = ? AND cancelled = 0",
            (room_code, date_str),
        ).fetchall()
        # 終了と開始が同じ時刻は重なりではない
        return any(parse_time(r["start"]) < end and start < parse_time(r["end"]) for r in rows)

    def _count_for_day(self, employee_no, date_str):
        return self.db.execute(
            "SELECT COUNT(*) FROM lounges_bookings WHERE employee_no = ? AND date = ? AND cancelled = 0",
            (employee_no, date_str),
        ).fetchone()[0]

    def active_booking(self, booking_id):
        try:
            number = int(booking_id)
        except (TypeError, ValueError):
            return None
        return self.db.execute("SELECT * FROM lounges_bookings WHERE id = ? AND cancelled = 0", (number,)).fetchone()

    def bookings(self, date_str=None):
        sql = "SELECT * FROM lounges_bookings WHERE cancelled = 0"
        args = []
        if date_str:
            sql += " AND date = ?"
            args.append(date_str)
        return self.db.execute(sql + " ORDER BY date, start, id", args).fetchall()

    def rooms(self):
        return self.db.execute("SELECT * FROM lounges_rooms ORDER BY code").fetchall()
