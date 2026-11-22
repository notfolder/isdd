"""来客用飲料の申請の判定。画面や DB には触れず、入力の検査と金額の計算だけを行う。"""

# 対象にできない社員の状態（総務規程 第 6 条）
EXCLUDED_STATUSES = {"retired"}

# 申請の状態
PENDING = "pending"
APPROVED = "approved"
REJECTED = "rejected"
STATES = (PENDING, APPROVED, REJECTED)

QUANTITY_RANGE = (1, 50)
UNIT_PRICE_RANGE = (1, 100000)


def with_tax(quantity, unit_price):
    """税込みの金額（消費税 10%、1 円未満は切り捨て）。"""
    return int(quantity * unit_price * 1.1)


class BeverageRules:
    """申請の受け付けと承認・却下の判定。受け付けないときは理由の文を返し、よいときは None を返す。"""

    @staticmethod
    def parse_int(text, low, high, label):
        """整数の欄を読む。(値, エラー文) を返す。"""
        text = (text or "").strip()
        if not (text.isascii() and text.isdigit()):
            return None, f"{label}は整数で入力してください"
        value = int(text)
        if not low <= value <= high:
            return None, f"{label}は {low} 以上 {high} 以下で入力してください"
        return value, None

    @staticmethod
    def check_employee(employee):
        """申請できる社員か。在籍していない社員や存在しない社員は対象にしない。"""
        if employee is None:
            return "社員が見つかりません"
        if employee["status"] in EXCLUDED_STATUSES:
            return "退職した社員は申請できません"
        return None

    @staticmethod
    def check_decidable(request_row):
        """承認・却下できる申請か。申請中のものにだけできる。"""
        if request_row is None:
            return "申請が見つかりません"
        if request_row["state"] != PENDING:
            return "申請中の申請だけ承認・却下できます"
        return None

    @classmethod
    def check_approver(cls, request_row, approver_no):
        """承認できるか。申請した本人は承認できない。"""
        error = cls.check_decidable(request_row)
        if error:
            return error
        if request_row["employee_no"] == approver_no:
            return "自分の申請は承認できません"
        return None
