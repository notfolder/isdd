"""印刷の申請の判定。画面や SQL には触れない。"""

MAX_QUANTITY = 1000
MAX_UNIT_PRICE = 100000


def parse_int(text, low, high):
    """半角数字だけの整数で、low 以上 high 以下なら整数を返す。そうでなければ None。"""
    text = (text or "").strip()
    if not (text.isascii() and text.isdigit()):
        return None
    value = int(text)
    return value if low <= value <= high else None


def parse_quantity(text):
    """数量（1 以上 1000 以下）。不正なら None。"""
    return parse_int(text, 1, MAX_QUANTITY)


def parse_unit_price(text):
    """税抜きの単価（1 以上 100000 以下、円）。不正なら None。"""
    return parse_int(text, 1, MAX_UNIT_PRICE)


def with_tax(quantity, unit_price):
    """税込みの金額。数量 × 単価に消費税 10% を足し、1 円未満を切り捨てる。"""
    return int(quantity * unit_price * 1.1)


def can_decide(state):
    """承認と却下ができるのは申請中のものだけ。"""
    return state == "pending"


def is_self_approval(applicant_no, approver_no):
    """承認する人が申請した本人か（本人は承認できない。却下はできる）。"""
    return applicant_no == approver_no
