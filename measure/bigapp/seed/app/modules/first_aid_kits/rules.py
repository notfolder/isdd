"""貸出の判定。画面や SQL には触れず、値だけを受け取って判定する。"""

import datetime

LOAN_DAYS = 7  # 貸出の期間（日）
MAX_LOANS_PER_PERSON = 1  # 1 人が同時に借りられる件数


def due_date(lent_on: datetime.date) -> datetime.date:
    """返却の期限。貸出日 + 7 日。"""
    return lent_on + datetime.timedelta(days=LOAN_DAYS)


def is_expired(due_on: datetime.date, today: datetime.date) -> bool:
    """期限切れか。今日が期限より後のときだけ真（期限当日は期限切れではない）。"""
    return today > due_on


def loan_status(loan, today: datetime.date) -> str:
    """物の状態。貸出が無ければ free、期限内なら lent、期限切れなら overdue。"""
    if loan is None:
        return "free"
    due_on = datetime.date.fromisoformat(loan["due_on"])
    return "overdue" if is_expired(due_on, today) else "lent"


def parse_lent_on(text, today: datetime.date):
    """貸出日を読む。省略なら今日。戻り値は (日付, エラー文)。"""
    text = (text or "").strip()
    if not text:
        return today, None
    try:
        value = datetime.date.fromisoformat(text)
    except ValueError:
        return None, "貸出日は YYYY-MM-DD の形で入力してください"
    if len(text) != 10:
        return None, "貸出日は YYYY-MM-DD の形で入力してください"
    if value > today:
        return None, "貸出日に未来の日付は指定できません"
    return value, None


def check_lend(item, employee, item_loan, employee_loans, today: datetime.date):
    """貸出できるか。できなければ理由の文を返し、できれば None。

    item: 物の行（無ければ None）、employee: 在籍の社員の行（無ければ None）、
    item_loan: その物の貸出中の記録、employee_loans: その社員が借りている貸出中の記録の一覧。
    """
    if employee is None:
        return "在籍している社員が見つかりません"
    if item is None:
        return "救急箱が見つかりません"
    if item_loan is not None:
        return "この救急箱は貸出中です"
    expired_loans = [
        loan for loan in employee_loans if is_expired(datetime.date.fromisoformat(loan["due_on"]), today)
    ]
    if expired_loans:
        return "返却の期限を過ぎた貸出があるため、新しく貸し出せません"
    if len(employee_loans) >= MAX_LOANS_PER_PERSON:
        return "この社員は既に借りています（同時に借りられるのは 1 件までです）"
    return None


def check_item_fields(code: str, name: str):
    """物の番号と名前の入力を確かめる。"""
    if not code:
        return "番号を入力してください"
    if not name:
        return "名前を入力してください"
    return None
