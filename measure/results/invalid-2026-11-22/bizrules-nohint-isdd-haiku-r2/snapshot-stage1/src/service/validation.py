"""画面の入力の形式と桁数を検査する。検査の結果は入力欄の名前から文言への辞書で返す。"""

import re
from datetime import date, datetime
from typing import Optional

EMPLOYEE_NUMBER_PATTERN = re.compile(r"[0-9]{6}")
EQUIPMENT_NUMBER_PATTERN = re.compile(r"[A-Za-z0-9-]{1,20}")
DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
PASSWORD_MIN_LENGTH = 8
NAME_MAX_LENGTH = 30
EQUIPMENT_NAME_MAX_LENGTH = 50


def validate_account_fields(employee_number: str, name: str, password: str) -> dict[str, str]:
    """利用者の登録の入力を検査する。

    社員番号は 6 桁の半角数字。名前は前後の空白を除いて 1〜30 文字。パスワードは 8 文字以上。
    引数 employee_number・name・password: 画面から送られた値（名前は前後の空白を含んだまま）。
    戻り値: 欄の名前から文言への辞書。問題が無ければ空の辞書。
    """
    errors: dict[str, str] = {}
    if not EMPLOYEE_NUMBER_PATTERN.fullmatch(employee_number):
        errors["employee_number"] = "社員番号は 6 桁の半角数字で入力してください"
    stripped = name.strip()
    if not 1 <= len(stripped) <= NAME_MAX_LENGTH:
        errors["name"] = f"名前は 1 文字以上 {NAME_MAX_LENGTH} 文字以内で入力してください"
    if len(password) < PASSWORD_MIN_LENGTH:
        errors["password"] = f"パスワードは {PASSWORD_MIN_LENGTH} 文字以上で入力してください"
    return errors


def validate_equipment_fields(equipment_number: str, name: str) -> dict[str, str]:
    """備品の登録と修正の入力を検査する。

    管理番号は半角の英数字とハイフンで 1〜20 文字（空白は不可）。備品名は前後の空白を除いて 1〜50 文字。
    引数 equipment_number・name: 画面から送られた値。
    戻り値: 欄の名前から文言への辞書。問題が無ければ空の辞書。
    """
    errors: dict[str, str] = {}
    if not EQUIPMENT_NUMBER_PATTERN.fullmatch(equipment_number):
        errors["equipment_number"] = "管理番号は半角の英数字とハイフンで 20 文字以内に入力してください"
    stripped = name.strip()
    if not 1 <= len(stripped) <= EQUIPMENT_NAME_MAX_LENGTH:
        errors["name"] = f"備品名は 1 文字以上 {EQUIPMENT_NAME_MAX_LENGTH} 文字以内で入力してください"
    return errors


def parse_lent_on(value: str) -> Optional[date]:
    """YYYY-MM-DD の文字列を日付にする。形式が違えば None。"""
    if not DATE_PATTERN.fullmatch(value):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def validate_lending_fields(borrower_raw: str, lent_on_raw: str,
                            today: date) -> tuple[dict[str, str], Optional[int], Optional[date]]:
    """貸出の登録の入力を検査し、解釈できた値も返す。

    借りる社員は必須（登録済みかは業務層が確かめる）。貸出日は必須、YYYY-MM-DD、今日以前。
    引数 borrower_raw: 選ばれた利用者の id（文字列）。
    引数 lent_on_raw: 貸出日（文字列）。
    引数 today: 日本時間の今日。
    戻り値: (欄の名前から文言への辞書, 利用者 id か None, 貸出日か None)。
    """
    errors: dict[str, str] = {}
    borrower_id: Optional[int] = None
    if borrower_raw.isdigit():
        borrower_id = int(borrower_raw)
    else:
        errors["borrower"] = "借りる社員を選んでください"

    lent_on: Optional[date] = None
    if not lent_on_raw:
        errors["lent_on"] = "貸出日を入力してください"
    else:
        lent_on = parse_lent_on(lent_on_raw)
        if lent_on is None:
            errors["lent_on"] = "貸出日は YYYY-MM-DD の形式で入力してください"
        elif lent_on > today:
            errors["lent_on"] = "貸出日は今日以前の日付を入力してください"
    return errors, borrower_id, lent_on
