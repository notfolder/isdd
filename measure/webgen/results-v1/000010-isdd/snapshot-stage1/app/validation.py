"""利用者名の検証。"""

MAX_NAME_LENGTH = 30
NAME_ERROR_MESSAGE = "Please enter your name (1–30 characters)."


def validate_player_name(raw):
    """前後の空白を除いた利用者名を返す。

    文字列でない、空、空白だけ、または 30 文字を超える場合は ValueError を送出する。
    """
    if not isinstance(raw, str):
        raise ValueError(NAME_ERROR_MESSAGE)
    name = raw.strip()
    if not 1 <= len(name) <= MAX_NAME_LENGTH:
        raise ValueError(NAME_ERROR_MESSAGE)
    return name
