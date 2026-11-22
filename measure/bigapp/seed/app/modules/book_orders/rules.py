"""書籍の購入の申請の判定。画面にも DB にも触れない関数だけを置く。"""

from decimal import ROUND_DOWN, Decimal

QUANTITY_MIN, QUANTITY_MAX = 1, 20
UNIT_PRICE_MIN, UNIT_PRICE_MAX = 1, 100000
TAX_RATE = Decimal("0.10")
STATES = ("pending", "approved", "rejected")
STATE_LABELS = {"pending": "申請中", "approved": "承認", "rejected": "却下"}


def parse_int(text, low, high):
    """整数の文字列を読み、low 以上 high 以下なら整数を、そうでなければ None を返す。"""
    text = (text or "").strip()
    if not text.isascii() or not text.lstrip("+-").isdigit():
        return None
    try:
        value = int(text)
    except ValueError:
        return None
    return value if low <= value <= high else None


def gross_amount(quantity, unit_price):
    """税込みの金額。数量 × 単価に消費税 10% を足し、1 円未満を切り捨てる。"""
    net = Decimal(quantity) * Decimal(unit_price)
    return int((net * (1 + TAX_RATE)).quantize(Decimal("1"), rounding=ROUND_DOWN))


def can_decide(state):
    """承認と却下ができるのは申請中のものだけ。"""
    return state == "pending"


def can_approve(state, applicant_no, approver_no):
    """承認できるか。申請中で、承認する人が申請した本人でないこと（総務規程 第 5 条）。"""
    return can_decide(state) and applicant_no != approver_no
