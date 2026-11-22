"""応接室の予約の判定。入力を受け付けてよいかを調べ、だめなら理由の文を返す。"""

import datetime
import re

# 予約の時間の単位（分）。開始も終了もこの倍数の時刻でなければならない。
UNIT = 30
OPEN_MINUTES = 9 * 60    # 9:00
CLOSE_MINUTES = 18 * 60  # 18:00
MAX_PER_DAY = 2          # 1 人が同じ日に取れる予約の数

_TIME = re.compile(r"^(\d{1,2}):(\d{2})$")


def parse_time(text):
    """HH:MM を分に直す。形が正しくなければ None。"""
    match = _TIME.match((text or "").strip())
    if not match:
        return None
    hour, minute = int(match.group(1)), int(match.group(2))
    if hour > 23 or minute > 59:
        return None
    return hour * 60 + minute


def format_time(minutes):
    """分を HH:MM に直す。"""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def parse_date(text):
    """YYYY-MM-DD を日付に直す。形が正しくなければ None。"""
    text = (text or "").strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        return None
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        return None


def check_time_range(start, end):
    """開始・終了の分を調べる。問題があれば理由、なければ None。"""
    if start % UNIT != 0 or end % UNIT != 0:
        return f"時刻は {UNIT} 分単位で指定してください"
    if start < OPEN_MINUTES or end > CLOSE_MINUTES:
        return "予約できるのは 9:00 から 18:00 の間です"
    if start >= end:
        return "開始は終了より前にしてください"
    return None


def check_not_past(date, today):
    """過去の日付は予約できない（今日はよい）。"""
    if date < today:
        return "過去の日付は予約できません"
    return None


def is_overlap(start, end, other_start, other_end):
    """時間が重なるか。終了と開始が同じ時刻なのは重なりではない。"""
    return start < other_end and other_start < end


def check_daily_limit(count):
    """その日にすでに取っている予約の数が上限に達していないか。"""
    if count >= MAX_PER_DAY:
        return f"1 人が 1 日に取れる予約は {MAX_PER_DAY} 件までです"
    return None
