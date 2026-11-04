"""入力の形式と長さの検査。エラーは項目名ごとの辞書で返す（空なら合格）。"""

import re
from datetime import date

EMPLOYEE_NUMBER_PATTERN = re.compile(r"[0-9]{7}")
EQUIPMENT_NUMBER_PATTERN = re.compile(r"[A-Za-z0-9-]{1,20}")
LENT_ON_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")

MSG_EMPLOYEE_NUMBER_FORMAT = "社員番号は 7 桁の数字で入力してください"
MSG_NAME_REQUIRED = "名前を入力してください"
MSG_NAME_TOO_LONG = "名前は 30 文字以内で入力してください"
MSG_PASSWORD_TOO_SHORT = "パスワードは 8 文字以上で入力してください"
MSG_EQUIPMENT_NUMBER_FORMAT = "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください"
MSG_EQUIPMENT_NAME_REQUIRED = "備品名を入力してください"
MSG_EQUIPMENT_NAME_TOO_LONG = "備品名は 50 文字以内で入力してください"
MSG_BORROWER_REQUIRED = "借りる社員を選んでください"
MSG_LENT_ON_FORMAT = "貸出日は YYYY-MM-DD の形で入力してください"
MSG_LENT_ON_FUTURE = "貸出日に未来の日付は入力できません"

NAME_MAX_LENGTH = 30
PASSWORD_MIN_LENGTH = 8
EQUIPMENT_NAME_MAX_LENGTH = 50


def validate_account_input(employee_number, name, password):
    """アカウント登録の入力を検査する。

    引数は前後の空白を取り除いた社員番号（7 桁の数字）と名前、取り除かないパスワード。
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


def validate_lending_input(borrower, lent_on_text, today):
    """貸出の登録の入力を検査する。

    引数 borrower は選んだ社員番号（空なら未選択）、lent_on_text は貸出日の文字列（YYYY-MM-DD）、
    today は日本時間の今日（date）。貸出日は今日と過去を受け付け、未来は受け付けない。
    戻り値は項目名（borrower・lent_on）から文言への辞書。空なら合格。
    """
    errors = {}
    if not borrower:
        errors["borrower"] = MSG_BORROWER_REQUIRED
    if not LENT_ON_PATTERN.fullmatch(lent_on_text):
        errors["lent_on"] = MSG_LENT_ON_FORMAT
    else:
        try:
            lent_on = date.fromisoformat(lent_on_text)
        except ValueError:
            errors["lent_on"] = MSG_LENT_ON_FORMAT
        else:
            if lent_on > today:
                errors["lent_on"] = MSG_LENT_ON_FUTURE
    return errors
