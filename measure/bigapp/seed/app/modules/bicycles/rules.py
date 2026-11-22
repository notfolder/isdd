"""社用自転車の貸出の判定。画面にも DB にも依存しない関数だけを置く。"""

import datetime

# 貸出の期間（日）。返却の期限 = 貸出日 + この日数
LOAN_DAYS = 1


def is_retired(employee) -> bool:
    """退職した社員なら True。"""
    return employee["status"] == "retired"


def clean(value) -> str:
    """フォームの入力の前後の空白を取る。"""
    return (value or "").strip()


def parse_date(text):
    """YYYY-MM-DD を日付にする。書式が違えば None。"""
    try:
        if len(text) != 10:
            return None
        return datetime.date.fromisoformat(text)
    except ValueError:
        return None


def due_date(lent_on: datetime.date) -> datetime.date:
    """貸出日から返却の期限を求める。"""
    return lent_on + datetime.timedelta(days=LOAN_DAYS)


def check_item_fields(code: str, name: str):
    """物の番号と名前の入力を調べる。問題があれば理由、無ければ None。"""
    if not code:
        return "番号を入力してください"
    if not name:
        return "名前を入力してください"
    return None
