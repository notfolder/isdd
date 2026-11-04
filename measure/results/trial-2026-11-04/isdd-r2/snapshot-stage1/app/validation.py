"""入力値の形式と桁数の検査。

各関数は問題が無ければ None、あれば利用者に見せる文言を返す。
"""

import re
from datetime import date
from typing import Optional

EMPLOYEE_NUMBER_PATTERN = re.compile(r"[0-9]{6}")
EQUIPMENT_NUMBER_PATTERN = re.compile(r"[A-Za-z0-9-]{1,20}")
DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
NAME_MAX_LENGTH = 30
PASSWORD_MIN_LENGTH = 8
EQUIPMENT_NAME_MAX_LENGTH = 50


def validate_employee_number(value: str) -> Optional[str]:
    """社員番号が 6 桁の数字かを検査する。

    Args:
        value: 入力された社員番号。

    Returns:
        問題があれば文言、無ければ None。
    """
    if EMPLOYEE_NUMBER_PATTERN.fullmatch(value) is None:
        return "社員番号は 6 桁の数字で入力してください"
    return None


def validate_name(value: str) -> Optional[str]:
    """名前が空でなく 30 文字以内かを検査する。前後の空白は除いて数える。

    Args:
        value: 入力された名前。

    Returns:
        問題があれば文言、無ければ None。
    """
    stripped = value.strip()
    if stripped == "":
        return "名前を入力してください"
    if len(stripped) > NAME_MAX_LENGTH:
        return "名前は 30 文字以内で入力してください"
    return None


def validate_password(value: str) -> Optional[str]:
    """パスワードが 8 文字以上かを検査する。

    Args:
        value: 入力されたパスワード。

    Returns:
        問題があれば文言、無ければ None。
    """
    if len(value) < PASSWORD_MIN_LENGTH:
        return "パスワードは 8 文字以上で入力してください"
    return None


def validate_equipment_number(value: str) -> Optional[str]:
    """管理番号が半角の英数字とハイフンで 20 文字以内かを検査する。

    Args:
        value: 入力された管理番号。

    Returns:
        問題があれば文言、無ければ None。
    """
    if EQUIPMENT_NUMBER_PATTERN.fullmatch(value) is None:
        return "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください"
    return None


def validate_equipment_name(value: str) -> Optional[str]:
    """備品名が空でなく 50 文字以内かを検査する。前後の空白は除いて数える。

    Args:
        value: 入力された備品名。

    Returns:
        問題があれば文言、無ければ None。
    """
    stripped = value.strip()
    if stripped == "":
        return "備品名を入力してください"
    if len(stripped) > EQUIPMENT_NAME_MAX_LENGTH:
        return "備品名は 50 文字以内で入力してください"
    return None


def validate_lent_on(value: str, today: date) -> Optional[str]:
    """貸出日が YYYY-MM-DD の実在する日付で、今日以前かを検査する。

    Args:
        value: 入力された貸出日。
        today: 今日の日付（日本時間）。

    Returns:
        問題があれば文言、無ければ None。
    """
    if value == "":
        return "貸出日を入力してください"
    if DATE_PATTERN.fullmatch(value) is None:
        return "貸出日は YYYY-MM-DD 形式で入力してください"
    try:
        lent_on = date.fromisoformat(value)
    except ValueError:
        return "貸出日は YYYY-MM-DD 形式で入力してください"
    if lent_on > today:
        return "貸出日に未来の日付は入力できません"
    return None
