"""貸出の判定をまとめる。画面や DB には触れない。"""

import datetime

LOAN_DAYS = 7  # 貸出の期間（日）
MAX_LOANS_PER_PERSON = 1  # 1 人が同時に借りられる件数


def is_retired(employee) -> bool:
    """退職した社員なら True。"""
    return employee["status"] != "active"


def days_past_due(due_on: datetime.date, today: datetime.date) -> int:
    """返却の期限を過ぎた日数。期限内なら 0。"""
    return max((today - due_on).days, 0)


class LendingRules:
    """貸出に関するきまりの判定。通らない場合は理由の文字列を返し、通れば None を返す。"""

    def __init__(self, today: datetime.date):
        self.today = today

    def due_on(self, lent_on: datetime.date) -> datetime.date:
        return lent_on + datetime.timedelta(days=LOAN_DAYS)

    def parse_lent_on(self, text: str):
        """貸出日を読む。省略なら今日。(日付, エラー) を返す。"""
        text = (text or "").strip()
        if not text:
            return self.today, None
        try:
            value = datetime.date.fromisoformat(text)
        except ValueError:
            return None, "貸出日は YYYY-MM-DD の形で入力してください"
        if value > self.today:
            return None, "貸出日に未来の日付は指定できません"
        return value, None

    def status(self, loan) -> str:
        """物の状態。loan は貸出中の記録（無ければ None）。free / lent / overdue。"""
        if loan is None:
            return "free"
        if days_past_due(datetime.date.fromisoformat(loan["due_on"]), self.today) > 0:
            return "overdue"
        return "lent"

    def check_borrower(self, employee, open_loans) -> "str | None":
        """借りる社員の判定。open_loans はその社員が持っている貸出中の記録。"""
        if employee is None:
            return "社員が見つかりません"
        if is_retired(employee):
            return "退職した社員には貸し出せません"
        for loan in open_loans:
            if days_past_due(datetime.date.fromisoformat(loan["due_on"]), self.today) > 0:
                return "返却の期限を過ぎた貸出があるため、新しく貸し出せません"
        if len(open_loans) >= MAX_LOANS_PER_PERSON:
            return "同時に借りられるのは 1 件までです"
        return None
