"""貸出の判定。DB には触らず、値だけで判断する。"""

import datetime

LOAN_DAYS = 7  # 貸出の期間（日）
MAX_LOANS_PER_PERSON = 2  # 1 人が同時に借りられる件数


def is_retired(employee) -> bool:
    """退職した社員かどうか。"""
    return employee["status"] == "retired"


def due_date(lent_on: datetime.date) -> datetime.date:
    """返却の期限。貸出日 + 7 日。"""
    return lent_on + datetime.timedelta(days=LOAN_DAYS)


def is_expired(due_on: datetime.date, today: datetime.date) -> bool:
    """返却の期限を過ぎているか（今日 > 期限）。期限の当日はまだ過ぎていない。"""
    return today > due_on


def parse_date(text):
    """YYYY-MM-DD を日付にする。形式が違えば None。"""
    try:
        if len(text) != 10:
            return None
        return datetime.date.fromisoformat(text)
    except (ValueError, TypeError):
        return None


def item_status(loan, today: datetime.date) -> str:
    """物の状態。貸出が無ければ free、期限内は lent、期限切れは overdue（status.json の値）。"""
    if loan is None:
        return "free"
    if is_expired(datetime.date.fromisoformat(loan["due_on"]), today):
        return "overdue"
    return "lent"


def check_lend(employee, item_loan, open_loans, lent_on, today):
    """貸出できなければ理由の文を返し、できれば None を返す。

    employee: 社員の行（無ければ None）、item_loan: その物の貸出中の行、
    open_loans: その社員が今持っている貸出の行のリスト。
    """
    if employee is None:
        return "社員が見つかりません"
    if is_retired(employee):
        return "退職した社員には貸し出せません"
    if lent_on is None:
        return "貸出日は YYYY-MM-DD の形で入力してください"
    if lent_on > today:
        return "貸出日に未来の日付は指定できません"
    if item_loan is not None:
        return "この物は貸出中です"
    if any(is_expired(datetime.date.fromisoformat(r["due_on"]), today) for r in open_loans):
        return "返却の期限を過ぎた貸出があるため、新しく貸し出せません"
    if len(open_loans) >= MAX_LOANS_PER_PERSON:
        return f"同時に借りられるのは {MAX_LOANS_PER_PERSON} 件までです"
    return None
