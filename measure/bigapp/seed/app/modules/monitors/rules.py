"""貸出の判定。DB には触れず、値だけで判定する。"""

import datetime

LOAN_DAYS = 30  # 貸出の期間（日）
MAX_LOANS = 2  # 1 人が同時に借りられる件数


def due_date(lent_on: datetime.date) -> datetime.date:
    """返却の期限（貸出日 + 30 日）。"""
    return lent_on + datetime.timedelta(days=LOAN_DAYS)


def is_late(due_on: datetime.date, today: datetime.date) -> bool:
    """返却の期限を過ぎているか（今日 > 期限）。"""
    late = today - due_on
    return late.days >= 1


def parse_lent_on(text, today: datetime.date):
    """貸出日を読む。省略は今日。(日付, エラー文) を返す。"""
    text = (text or "").strip()
    if not text:
        return today, None
    try:
        lent_on = datetime.date.fromisoformat(text)
    except ValueError:
        return None, "貸出日は YYYY-MM-DD の形で入力してください"
    if lent_on > today:
        return None, "未来の日付は貸出日にできません"
    return lent_on, None


def check_lend(item, employee, open_loans, today: datetime.date):
    """貸出できるか判定する。できなければ理由、できれば None。

    item: 物の行（なければ None）、employee: 在籍の社員の行（なければ None）、
    open_loans: その社員が今借りている貸出の行のリスト。
    """
    if item is None:
        return "物が見つかりません"
    if employee is None:
        return "在籍している社員が見つかりません"
    if len(open_loans) >= MAX_LOANS:
        return f"同時に借りられるのは {MAX_LOANS} 件までです"
    if any(is_late(date_of(row["due_on"]), today) for row in open_loans):
        return "返却の期限を過ぎた貸出があるため、貸し出せません（late_return）"
    return None


def date_of(text: str) -> datetime.date:
    return datetime.date.fromisoformat(text)


def status_of(open_loan, today: datetime.date) -> str:
    """物の状態。free / lent / overdue（期限超過）。"""
    if open_loan is None:
        return "free"
    return "overdue" if is_late(date_of(open_loan["due_on"]), today) else "lent"
