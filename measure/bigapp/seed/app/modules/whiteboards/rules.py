"""貸出のきまりの判定。DB には触らず、値だけを見て理由（エラー文）か None を返す。"""

import datetime

LOAN_DAYS = 7  # 貸出の期間（日）
MAX_LOANS = 2  # 1 人が同時に借りられる件数


def due_date(lent_on: datetime.date) -> datetime.date:
    """返却の期限 = 貸出日 + 7 日。"""
    return lent_on + datetime.timedelta(days=LOAN_DAYS)


def parse_lent_on(text: str, today: datetime.date):
    """貸出日の文字列を日付にする。省略は今日。(日付, エラー) を返す。"""
    text = (text or "").strip()
    if not text:
        return today, None
    try:
        day = datetime.date.fromisoformat(text)
    except ValueError:
        return None, "貸出日は YYYY-MM-DD の形で入力してください"
    if day > today:
        return None, "貸出日に未来の日付は指定できません"
    return day, None


def check_lend(item, employee, lent_on_error, active_count: int, overdue_count: int):
    """貸出できない理由を返す。できるなら None。item・employee は行（無ければ None）。"""
    if item is None:
        return "物が見つかりません"
    if employee is None:
        return "在籍している社員が見つかりません"
    if lent_on_error:
        return lent_on_error
    if item["state"] != "free":
        return "この物は貸出中です"
    if overdue_count > 0:
        return "返却の期限を過ぎた貸出があるため、新しく貸し出せません"
    if active_count >= MAX_LOANS:
        return f"同時に借りられるのは {MAX_LOANS} 件までです"
    return None
