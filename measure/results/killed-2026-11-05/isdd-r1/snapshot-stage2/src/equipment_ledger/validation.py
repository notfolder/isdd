"""入力の検証。前後の空白を除いてから判定し、項目ごとの文言を返す。"""

import re
from datetime import date, datetime, timedelta, timezone

EMPLOYEE_NUMBER_PATTERN = re.compile(r"[0-9]{7}")
EQUIPMENT_NUMBER_PATTERN = re.compile(r"[A-Za-z0-9-]{1,20}")
LENT_ON_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
PASSWORD_MIN_LENGTH = 8
NAME_MAX_LENGTH = 30
EQUIPMENT_NAME_MAX_LENGTH = 50
JAPAN_TIMEZONE = timezone(timedelta(hours=9))


def _strip(value):
    return (value or "").strip()


def today_in_japan():
    """日本時間（UTC+9）の今日の日付を返す。貸出日の既定値と未来の判定の基準にする。"""
    return datetime.now(JAPAN_TIMEZONE).date()


def validate_account_input(employee_number, name, password):
    """アカウント登録の入力を検証する。

    戻り値は (値の辞書, 文言の辞書)。文言の辞書は項目名から文言への対応で、空なら入力は正しい。
    社員番号は 7 桁の数字。パスワードは空白を除かず、そのまま扱う。
    """
    values = {
        "employee_number": _strip(employee_number),
        "name": _strip(name),
        "password": password or "",
    }
    errors = {}
    if not EMPLOYEE_NUMBER_PATTERN.fullmatch(values["employee_number"]):
        errors["employee_number"] = "社員番号は 7 桁の数字で入力してください"
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


def validate_lending_input(borrower_id, lent_on, today):
    """貸出の入力を検証する。today は貸出日の上限（日本時間の今日）。

    戻り値は (値の辞書, 文言の辞書)。値の辞書の borrower_id は整数、未選択なら None。
    借りる社員が実在するかは貸出の処理（lending.lend_equipment）で確かめる。
    """
    text_borrower = _strip(borrower_id)
    text_lent_on = _strip(lent_on)
    values = {
        "borrower_id": int(text_borrower) if text_borrower.isdigit() else None,
        "lent_on": text_lent_on,
    }
    errors = {}
    if values["borrower_id"] is None:
        errors["borrower_id"] = "借りる社員を選んでください"
    if not text_lent_on:
        errors["lent_on"] = "貸出日を入力してください"
    elif not LENT_ON_PATTERN.fullmatch(text_lent_on):
        errors["lent_on"] = "貸出日は YYYY-MM-DD の形式で入力してください"
    else:
        try:
            parsed = date.fromisoformat(text_lent_on)
        except ValueError:
            errors["lent_on"] = "貸出日は YYYY-MM-DD の形式で入力してください"
        else:
            if parsed > today:
                errors["lent_on"] = "貸出日に未来の日付は入力できません"
    return values, errors
