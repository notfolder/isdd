"""屋上予約の判定。画面にも DB にも触れない関数だけを置く。"""

import datetime

SLOT_MINUTES = 60  # 予約の時間の単位（分）
OPEN_MINUTE = 9 * 60  # 9:00
CLOSE_MINUTE = 18 * 60  # 18:00
MAX_BOOKINGS_PER_DAY = 1  # 1 人が 1 日に取れる予約の数
EXCLUDED_STATUSES = {"retired"}  # 予約の対象にしない社員の状態


class RuleError(Exception):
    """入力を受け付けられない理由。message を画面に出す。"""


def parse_date(text):
    """YYYY-MM-DD を日付にする。形が違えば RuleError。"""
    text = (text or "").strip()
    if len(text) != 10:
        raise RuleError("日付は YYYY-MM-DD で入力してください")
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        raise RuleError("日付は YYYY-MM-DD で入力してください")


def parse_time(text):
    """HH:MM を 0 時からの分にする。形が違えば RuleError。"""
    text = (text or "").strip()
    parts = text.split(":")
    if len(parts) != 2 or not all(p.isdigit() and len(p) == 2 for p in parts):
        raise RuleError("時刻は HH:MM で入力してください")
    hour, minute = int(parts[0]), int(parts[1])
    if hour > 23 or minute > 59:
        raise RuleError("時刻は HH:MM で入力してください")
    return hour * 60 + minute


def format_minute(minute):
    """0 時からの分を HH:MM にする。"""
    return f"{minute // 60:02d}:{minute % 60:02d}"


def check_slot(start, end):
    """時間の単位・営業時間・前後関係を確かめる。start と end は分。"""
    if start % SLOT_MINUTES or end % SLOT_MINUTES:
        raise RuleError(f"予約は {SLOT_MINUTES} 分の単位で取ってください")
    if start < OPEN_MINUTE or end > CLOSE_MINUTE:
        raise RuleError("予約は 9:00 から 18:00 の間で取ってください")
    if start >= end:
        raise RuleError("終了は開始より後にしてください")


def check_not_past(date, today):
    """過去の日付は予約できない（今日はよい）。"""
    if date < today:
        raise RuleError("過去の日付は予約できません")


def overlaps(start, end, other_start, other_end):
    """2 つの時間帯が重なるか。終了と開始が同じ時刻なら重ならない。"""
    return start < other_end and other_start < end


def is_eligible(status):
    """在籍している（予約の対象にできる）社員か。"""
    return status not in EXCLUDED_STATUSES
