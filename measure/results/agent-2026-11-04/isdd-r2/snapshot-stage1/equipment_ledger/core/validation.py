"""入力チェック。失敗した欄ごとに文言を返す。"""

import re

EMPLOYEE_NUMBER_RE = re.compile(r"[0-9]{6}")
EQUIPMENT_NUMBER_RE = re.compile(r"[A-Za-z0-9-]{1,20}")

MSG_EMPLOYEE_NUMBER_FORMAT = "社員番号は 6 桁の数字で入力してください"
MSG_NAME_REQUIRED = "名前を入力してください"
MSG_NAME_TOO_LONG = "名前は 30 文字以内で入力してください"
MSG_PASSWORD_TOO_SHORT = "パスワードは 8 文字以上で入力してください"
MSG_EQUIPMENT_NUMBER_FORMAT = "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください"
MSG_EQUIPMENT_NAME_REQUIRED = "備品名を入力してください"
MSG_EQUIPMENT_NAME_TOO_LONG = "備品名は 50 文字以内で入力してください"


def validate_account_input(employee_number: str, name: str, password: str) -> dict[str, str]:
    """アカウント登録の入力を検査する。欄名から文言への辞書を返す（問題が無ければ空）。"""
    errors: dict[str, str] = {}
    if not EMPLOYEE_NUMBER_RE.fullmatch(employee_number):
        errors["employee_number"] = MSG_EMPLOYEE_NUMBER_FORMAT
    stripped = name.strip()
    if not stripped:
        errors["name"] = MSG_NAME_REQUIRED
    elif len(stripped) > 30:
        errors["name"] = MSG_NAME_TOO_LONG
    if len(password) < 8:
        errors["password"] = MSG_PASSWORD_TOO_SHORT
    return errors


def validate_equipment_input(equipment_number: str, name: str) -> dict[str, str]:
    """備品の登録・修正の入力を検査する。欄名から文言への辞書を返す（問題が無ければ空）。"""
    errors: dict[str, str] = {}
    if equipment_number is not None and not EQUIPMENT_NUMBER_RE.fullmatch(equipment_number):
        errors["equipment_number"] = MSG_EQUIPMENT_NUMBER_FORMAT
    stripped = name.strip()
    if not stripped:
        errors["name"] = MSG_EQUIPMENT_NAME_REQUIRED
    elif len(stripped) > 50:
        errors["name"] = MSG_EQUIPMENT_NAME_TOO_LONG
    return errors
