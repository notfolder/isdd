"""茶菓の申請の判定。画面や DB の更新からは切り離し、受け付けてよいかだけを決める。"""

MIN_QUANTITY, MAX_QUANTITY = 1, 100
MIN_PRICE, MAX_PRICE = 1, 100000
STATES = ("pending", "approved", "rejected")


def parse_int(text):
    """半角数字だけの文字列を整数にする。それ以外は None。"""
    text = (text or "").strip()
    return int(text) if text.isascii() and text.isdigit() else None


def is_retired(employee):
    """社員が退職しているか。"""
    return employee["status"] == "retired"


class SnackRules:
    """申請・承認・却下を受け付けてよいかの判定。受け付けないときは理由の文字列を返し、よければ None。"""

    @staticmethod
    def check_apply(employee, quantity, unit_price):
        if employee is None:
            return "社員が見つかりません"
        if is_retired(employee):
            return "退職した社員は申請できません"
        if quantity is None or not (MIN_QUANTITY <= quantity <= MAX_QUANTITY):
            return "数量は 1 以上 100 以下の整数で入力してください"
        if unit_price is None or not (MIN_PRICE <= unit_price <= MAX_PRICE):
            return "単価は 1 以上 100000 以下の整数で入力してください"
        return None

    @staticmethod
    def check_decide(request_row):
        """承認・却下に共通の判定。申請中のものにだけできる。"""
        if request_row is None:
            return "申請が見つかりません"
        if request_row["state"] != "pending":
            return "申請中の申請ではありません"
        return None

    @classmethod
    def check_approve(cls, request_row, approver):
        error = cls.check_decide(request_row)
        if error:
            return error
        if request_row["employee_no"] == approver["employee_no"]:
            return "自分の申請は承認できません"
        return None
