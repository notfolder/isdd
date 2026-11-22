"""ケータリング申請の判定。入力の検査と、状態ごとの可否をここにまとめる。"""

import re

STATES = ("pending", "approved", "rejected")
QUANTITY_MIN, QUANTITY_MAX = 1, 200
UNIT_PRICE_MIN, UNIT_PRICE_MAX = 1, 100000

_DIGITS = re.compile(r"[0-9]+")


def is_retired(employee) -> bool:
    """退職した社員なら True。"""
    return employee["status"] == "retired"


class CateringRules:
    """申請の受付と承認・却下の可否を判定する。受け付けられないときは理由の文を返す。"""

    @staticmethod
    def parse_int(text, low, high):
        """整数として読み、low 以上 high 以下なら値を返す。そうでなければ None。"""
        text = (text or "").strip()
        if not _DIGITS.fullmatch(text):
            return None
        value = int(text)
        return value if low <= value <= high else None

    @classmethod
    def parse_quantity(cls, text):
        return cls.parse_int(text, QUANTITY_MIN, QUANTITY_MAX)

    @classmethod
    def parse_unit_price(cls, text):
        return cls.parse_int(text, UNIT_PRICE_MIN, UNIT_PRICE_MAX)

    @staticmethod
    def check_applicant(employee):
        """申請できる社員か。できなければ理由を返す。"""
        if employee is None:
            return "社員が見つかりません"
        if not is_retired(employee):
            return None
        return "退職した社員は申請できません"

    @staticmethod
    def check_decidable(request_row):
        """承認・却下の対象にできる申請か（申請中のものだけ）。"""
        if request_row is None:
            return "申請が見つかりません"
        if request_row["state"] != "pending":
            return "申請中の申請だけ承認・却下できます"
        return None

    @classmethod
    def check_approve(cls, request_row, approver_no):
        """承認できるか。申請した本人は承認できない。"""
        error = cls.check_decidable(request_row)
        if error:
            return error
        if request_row["employee_no"] == approver_no:
            return "申請した本人は承認できません"
        return None
