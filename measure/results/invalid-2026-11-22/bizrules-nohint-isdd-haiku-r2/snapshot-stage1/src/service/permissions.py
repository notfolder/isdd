"""担当者だけが行える操作の権限を確かめる。"""

from typing import Optional

from service.accounts import MANAGER_ROLE, User

PERMISSION_DENIED_MESSAGE = "この操作は担当者だけができます"


class PermissionDenied(Exception):
    """利用者に権限が無い操作を行おうとしたことを表す例外。画面では 403 にする。"""


def require_manager(actor: Optional[User]) -> None:
    """利用者が担当者でなければ PermissionDenied を投げる。

    引数 actor: 操作する利用者。未ログイン（None）も拒否する。
    """
    if actor is None or actor.role != MANAGER_ROLE:
        raise PermissionDenied(PERMISSION_DENIED_MESSAGE)
