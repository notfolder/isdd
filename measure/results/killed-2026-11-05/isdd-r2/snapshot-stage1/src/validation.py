"""入力の形式と長さの検査。エラーは項目名ごとの辞書で返す（空なら合格）。"""

import re

EMPLOYEE_NUMBER_PATTERN = re.compile(r"[0-9]{6}")
EQUIPMENT_NUMBER_PATTERN = re.compile(r"[A-Za-z0-9-]{1,20}")

MSG_EMPLOYEE_NUMBER_FORMAT = "社員番号は 6 桁の数字で入力してください"
MSG_NAME_REQUIRED = "名前を入力してください"
MSG_NAME_TOO_LONG = "名前は 30 文字以内で入力してください"
MSG_PASSWORD_TOO_SHORT = "パスワードは 8 文字以上で入力してください"
MSG_EQUIPMENT_NUMBER_FORMAT = "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください"
MSG_EQUIPMENT_NAME_REQUIRED = "備品名を入力してください"
MSG_EQUIPMENT_NAME_TOO_LONG = "備品名は 50 文字以内で入力してください"

NAME_MAX_LENGTH = 30
PASSWORD_MIN_LENGTH = 8
EQUIPMENT_NAME_MAX_LENGTH = 50


def validate_account_input(employee_number, name, password):
    """アカウント登録の入力を検査する。

    引数は前後の空白を取り除いた社員番号と名前、取り除かないパスワード。
    戻り値は項目名（employee_number・name・password）から文言への辞書。
    """
    errors = {}
    if not EMPLOYEE_NUMBER_PATTERN.fullmatch(employee_number):
        errors["employee_number"] = MSG_EMPLOYEE_NUMBER_FORMAT
    if not name:
        errors["name"] = MSG_NAME_REQUIRED
    elif len(name) > NAME_MAX_LENGTH:
        errors["name"] = MSG_NAME_TOO_LONG
    if len(password) < PASSWORD_MIN_LENGTH:
        errors["password"] = MSG_PASSWORD_TOO_SHORT
    return errors


def validate_equipment_input(equipment_number, name):
    """備品の登録・修正の入力を検査する。

    引数は前後の空白を取り除いた管理番号と備品名。
    戻り値は項目名（equipment_number・name）から文言への辞書。重複は検査しない。
    """
    errors = {}
    if not EQUIPMENT_NUMBER_PATTERN.fullmatch(equipment_number):
        errors["equipment_number"] = MSG_EQUIPMENT_NUMBER_FORMAT
    if not name:
        errors["name"] = MSG_EQUIPMENT_NAME_REQUIRED
    elif len(name) > EQUIPMENT_NAME_MAX_LENGTH:
        errors["name"] = MSG_EQUIPMENT_NAME_TOO_LONG
    return errors
