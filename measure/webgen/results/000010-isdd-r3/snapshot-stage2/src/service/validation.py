"""利用者名の規則。"""

from typing import Any

NAME_MIN_LENGTH = 1
NAME_MAX_LENGTH = 20
NAME_ERROR_MESSAGE = "Please enter a name of 1 to 20 characters."


class PlayerNameError(ValueError):
    """利用者名が規則に合わないことを表す。"""


def validate_player_name(raw: Any) -> str:
    """前後の空白を除いた利用者名を返す。文字列でない、または規則に合わなければ PlayerNameError を投げる。"""
    if not isinstance(raw, str):
        raise PlayerNameError(NAME_ERROR_MESSAGE)
    name = raw.strip()
    if not NAME_MIN_LENGTH <= len(name) <= NAME_MAX_LENGTH:
        raise PlayerNameError(NAME_ERROR_MESSAGE)
    return name
