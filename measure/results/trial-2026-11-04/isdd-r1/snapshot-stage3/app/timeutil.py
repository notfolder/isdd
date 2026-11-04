"""日付の扱い。業務上の「今日」は日本時間で決める。"""

from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))


def today_jst() -> str:
    """日本時間の今日を YYYY-MM-DD で返す。"""
    return datetime.now(JST).date().isoformat()
