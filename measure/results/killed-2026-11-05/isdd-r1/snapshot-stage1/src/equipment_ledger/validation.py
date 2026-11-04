"""入力の検証。前後の空白を除いてから判定し、項目ごとの文言を返す。"""

import re

EMPLOYEE_NUMBER_PATTERN = re.compile(r"[0-9]{6}")
EQUIPMENT_NUMBER_PATTERN = re.compile(r"[A-Za-z0-9-]{1,20}")
PASSWORD_MIN_LENGTH = 8
NAME_MAX_LENGTH = 30
EQUIPMENT_NAME_MAX_LENGTH = 50


def _strip(value):
    return (value or "").strip()


def validate_account_input(employee_number, name, password):
    """アカウント登録の入力を検証する。

    戻り値は (値の辞書, 文言の辞書)。文言の辞書は項目名から文言への対応で、空なら入力は正しい。
    パスワードは空白を除かず、そのまま扱う。
    """
    values = {
        "employee_number": _strip(employee_number),
        "name": _strip(name),
        "password": password or "",
    }
    errors = {}
    if not EMPLOYEE_NUMBER_PATTERN.fullmatch(values["employee_number"]):
        errors["employee_number"] = "社員番号は 6 桁の数字で入力してください"
    if not values["name"]:
        errors["name"] = "名前を入力してください"
    elif len(values["name"]) > NAME_MAX_LENGTH:
        errors["name"] = "名前は 30 文字以内で入力してください"
    if len(values["password"]) < PASSWORD_MIN_LENGTH:
        errors["password"] = "パスワードは 8 文字以上で入力してください"
    return values, errors


def validate_equipment_input(equipment_number, name):
    """備品の入力を検証する。戻り値の形は validate_account_input と同じ。"""
    values = {
        "equipment_number": _strip(equipment_number),
        "name": _strip(name),
    }
    errors = {}
    if not EQUIPMENT_NUMBER_PATTERN.fullmatch(values["equipment_number"]):
        errors["equipment_number"] = "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください"
    if not values["name"]:
        errors["name"] = "備品名を入力してください"
    elif len(values["name"]) > EQUIPMENT_NAME_MAX_LENGTH:
        errors["name"] = "備品名は 50 文字以内で入力してください"
    return values, errors
