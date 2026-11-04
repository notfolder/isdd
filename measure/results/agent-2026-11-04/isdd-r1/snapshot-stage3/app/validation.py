"""入力値の形式と桁数の検査。重複の検査は DB 側で行う。"""

import datetime
import re
from typing import Dict

EMPLOYEE_NUMBER_PATTERN = re.compile(r"[0-9]{6}")
EQUIPMENT_NUMBER_PATTERN = re.compile(r"[A-Za-z0-9-]{1,20}")

MSG_EMPLOYEE_NUMBER_FORMAT = "社員番号は 6 桁の数字で入力してください"
MSG_EMPLOYEE_NUMBER_DUPLICATE = "この社員番号は既に登録されています"
MSG_NAME_REQUIRED = "名前を入力してください"
MSG_NAME_TOO_LONG = "名前は 30 文字以内で入力してください"
MSG_PASSWORD_TOO_SHORT = "パスワードは 8 文字以上で入力してください"
MSG_EQUIPMENT_NUMBER_FORMAT = "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください"
MSG_EQUIPMENT_NUMBER_DUPLICATE = "この管理番号は既に使われています"
MSG_EQUIPMENT_NAME_REQUIRED = "備品名を入力してください"
MSG_EQUIPMENT_NAME_TOO_LONG = "備品名は 50 文字以内で入力してください"

NAME_MAX_LENGTH = 30
PASSWORD_MIN_LENGTH = 8
EQUIPMENT_NAME_MAX_LENGTH = 50

BORROWER_ID_PATTERN = re.compile(r"[0-9]+")
LENT_ON_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
MSG_BORROWER_REQUIRED = "借りる社員を選んでください"
MSG_LENT_ON_FORMAT = "貸出日は YYYY-MM-DD の形式で入力してください"
MSG_LENT_ON_FUTURE = "貸出日に未来の日付は入力できません"


def validate_account_input(employee_number: str, name: str, password: str) -> Dict[str, str]:
    """アカウント登録の入力を検査し、入力欄名から文言への辞書を返す（空なら合格）。"""
    errors: Dict[str, str] = {}
    if not EMPLOYEE_NUMBER_PATTERN.fullmatch(employee_number):
        errors["employee_number"] = MSG_EMPLOYEE_NUMBER_FORMAT
    stripped = name.strip()
    if stripped == "":
        errors["name"] = MSG_NAME_REQUIRED
    elif len(stripped) > NAME_MAX_LENGTH:
        errors["name"] = MSG_NAME_TOO_LONG
    if len(password) < PASSWORD_MIN_LENGTH:
        errors["password"] = MSG_PASSWORD_TOO_SHORT
    return errors


def validate_password(password: str) -> Dict[str, str]:
    """パスワードの長さを検査する（8 文字以上）。戻り値は入力欄名から文言への辞書（空なら合格）。"""
    if len(password) < PASSWORD_MIN_LENGTH:
        return {"password": MSG_PASSWORD_TOO_SHORT}
    return {}


def validate_equipment_input(equipment_number: str, name: str) -> Dict[str, str]:
    """備品の登録・修正の入力を検査し、入力欄名から文言への辞書を返す（空なら合格）。"""
    errors: Dict[str, str] = {}
    if not EQUIPMENT_NUMBER_PATTERN.fullmatch(equipment_number):
        errors["equipment_number"] = MSG_EQUIPMENT_NUMBER_FORMAT
    stripped = name.strip()
    if stripped == "":
        errors["name"] = MSG_EQUIPMENT_NAME_REQUIRED
    elif len(stripped) > EQUIPMENT_NAME_MAX_LENGTH:
        errors["name"] = MSG_EQUIPMENT_NAME_TOO_LONG
    return errors


def validate_loan_input(borrower_id: str, lent_on: str, today: datetime.date) -> Dict[str, str]:
    """貸出の登録の入力を検査する。借りる社員の存在は DB 側で確かめる。戻り値は入力欄名から文言への辞書。"""
    errors: Dict[str, str] = {}
    if not BORROWER_ID_PATTERN.fullmatch(borrower_id):
        errors["borrower"] = MSG_BORROWER_REQUIRED
    if not LENT_ON_PATTERN.fullmatch(lent_on):
        errors["lent_on"] = MSG_LENT_ON_FORMAT
    else:
        try:
            lent_date = datetime.date.fromisoformat(lent_on)
        except ValueError:
            errors["lent_on"] = MSG_LENT_ON_FORMAT
        else:
            if lent_date > today:
                errors["lent_on"] = MSG_LENT_ON_FUTURE
    return errors
