"""今日の日付。環境変数 APP_TODAY（YYYY-MM-DD）があればそれを今日として扱う（確認用）。"""

import datetime
import os
from zoneinfo import ZoneInfo


def today() -> datetime.date:
    fixed = os.environ.get("APP_TODAY")
    if fixed:
        return datetime.date.fromisoformat(fixed)
    return datetime.datetime.now(ZoneInfo("Asia/Tokyo")).date()


def now_text() -> str:
    return datetime.datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds")
