"""入力の検証。入力欄ごとのエラー文言を返す（文言は設計書の文言と完全一致させる）。

呼び出し側は、前後の空白を除いてから渡す（パスワードだけは除かない）。
"""

import re

from .timeutil import today_jst

EMPLOYEE_NUMBER_RE = re.compile(r"[0-9]{6}")
EQUIPMENT_NUMBER_RE = re.compile(r"[A-Za-z0-9-]{1,20}")
NAME_MAX_LENGTH = 30
EQUIPMENT_NAME_MAX_LENGTH = 50
PASSWORD_MIN_LENGTH = 8
DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def validate_account_input(employee_number: str, name: str, password: str) -> dict[str, str]:
    """アカウント登録の入力を検証し、入力欄の名前ごとのエラー文言を返す。問題が無ければ空。"""
    errors: dict[str, str] = {}
    if not EMPLOYEE_NUMBER_RE.fullmatch(employee_number):
        errors["employee_number"] = "社員番号は 6 桁の数字で入力してください"
    if not name:
        errors["name"] = "名前を入力してください"
    elif len(name) > NAME_MAX_LENGTH:
        errors["name"] = "名前は 30 文字以内で入力してください"
    password_error = validate_password(password)
    if password_error:
        errors["password"] = password_error
    return errors


def validate_password(password: str) -> str | None:
    """パスワードを検証する。問題があれば文言、無ければ None。"""
    if len(password) < PASSWORD_MIN_LENGTH:
        return "パスワードは 8 文字以上で入力してください"
    return None


def validate_equipment_input(equipment_number: str, name: str) -> dict[str, str]:
    """備品の登録・修正の入力を検証する。入力欄の名前ごとのエラー文言を返す。"""
    errors: dict[str, str] = {}
    if not EQUIPMENT_NUMBER_RE.fullmatch(equipment_number):
        errors["equipment_number"] = "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください"
    if not name:
        errors["name"] = "備品名を入力してください"
    elif len(name) > EQUIPMENT_NAME_MAX_LENGTH:
        errors["name"] = "備品名は 50 文字以内で入力してください"
    return errors


def validate_lent_on(lent_on: str, today: str | None = None) -> str | None:
    """貸出日を検証する。形式が違えば文言、未来の日付なら文言、問題が無ければ None。

    today は日本時間の今日（省略時は今日）を YYYY-MM-DD で渡す。
    """
    if not DATE_RE.fullmatch(lent_on):
        return "貸出日は日付で入力してください"
    if today is None:
        today = today_jst()
    if lent_on > today:
        return "貸出日に未来の日付は入力できません"
    return None
