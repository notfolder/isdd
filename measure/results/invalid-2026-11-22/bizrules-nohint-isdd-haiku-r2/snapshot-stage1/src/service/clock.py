"""日本時間（Asia/Tokyo）の現在時刻を返す。"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")


def now_jst() -> datetime:
    """日本時間の現在時刻（タイムゾーン付き）を返す。"""
    return datetime.now(JST)


def today_jst() -> date:
    """日本時間の今日の日付を返す。貸出日の既定値と、未来日の判定に使う。"""
    return now_jst().date()
