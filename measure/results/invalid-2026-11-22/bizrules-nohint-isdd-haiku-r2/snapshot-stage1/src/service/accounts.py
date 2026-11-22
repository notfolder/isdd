"""利用者アカウントの登録と認証を行う。パスワードは scrypt のハッシュでだけ保存する。"""

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Optional

from data.database import Database
from data.repositories import DuplicateError, UserRepository
from service.clock import now_jst
from service.errors import ServiceError
from service.validation import validate_account_fields

MANAGER_ROLE = "manager"
MEMBER_ROLE = "member"
LOGIN_FAILED_MESSAGE = "社員番号またはパスワードが違います"
DUPLICATE_EMPLOYEE_NUMBER_MESSAGE = "この社員番号は登録されています"

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 32
SCRYPT_SALT_BYTES = 16


@dataclass(frozen=True)
class User:
    """ログイン中の利用者を表す値。"""

    id: int
    employee_number: str
    name: str
    role: str


def hash_password(password: str) -> str:
    """パスワードを scrypt でハッシュし、保存用の 1 つの文字列にする。

    形式: scrypt$N$r$p$ソルト（16 進）$ハッシュ（16 進）。元のパスワードは含まれない。
    """
    salt = secrets.token_bytes(SCRYPT_SALT_BYTES)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R,
                            p=SCRYPT_P, dklen=SCRYPT_DKLEN)
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """パスワードが保存済みのハッシュと一致するかを返す。比較は一定時間で行う。"""
    try:
        _, n, r, p, salt_hex, digest_hex = stored.split("$")
        digest = hashlib.scrypt(password.encode("utf-8"), salt=bytes.fromhex(salt_hex),
                                n=int(n), r=int(r), p=int(p), dklen=len(digest_hex) // 2)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)


def _to_user(row) -> User:
    return User(id=int(row["id"]), employee_number=row["employee_number"],
                name=row["name"], role=row["role"])


class AccountService:
    """利用者アカウントの登録、認証、取り出しを行う。"""

    def __init__(self, db: Database, users: UserRepository) -> None:
        """引数 db: データベース。引数 users: 利用者の表の操作。"""
        self._db = db
        self._users = users

    def register(self, employee_number: str, name: str, password: str) -> None:
        """利用者を登録する。最初の 1 件は担当者、2 件目以降は社員にする。

        入力の検査に失敗したら、入力欄ごとの文言を持つ ServiceError を投げる。
        同時の登録は書き込みの排他で直列化するので、担当者は 1 人だけになる。
        """
        errors = validate_account_fields(employee_number, name, password)
        if errors:
            raise ServiceError(field_errors=errors)
        created_at = now_jst().isoformat(timespec="seconds")
        try:
            with self._db.transaction() as conn:
                role = MANAGER_ROLE if self._users.count(conn) == 0 else MEMBER_ROLE
                self._users.insert(conn, employee_number, name.strip(), hash_password(password),
                                   role, created_at)
        except DuplicateError:
            raise ServiceError(field_errors={"employee_number": DUPLICATE_EMPLOYEE_NUMBER_MESSAGE})

    def authenticate(self, employee_number: str, password: str) -> User:
        """社員番号とパスワードで利用者を認証する。

        社員番号が無い場合と、パスワードが違う場合は同じ文言の ServiceError を投げる。
        """
        with self._db.connection() as conn:
            row = self._users.find_by_employee_number(conn, employee_number)
        if row is None or not verify_password(password, row["password_hash"]):
            raise ServiceError(message=LOGIN_FAILED_MESSAGE)
        return _to_user(row)

    def find_by_id(self, user_id: int) -> Optional[User]:
        """id で利用者を探す。無ければ None。"""
        with self._db.connection() as conn:
            row = self._users.find_by_id(conn, user_id)
        return _to_user(row) if row is not None else None

    def list_borrowers(self) -> list[User]:
        """貸出の相手に選べる全利用者を、社員番号の昇順で返す。"""
        with self._db.connection() as conn:
            return [_to_user(row) for row in self._users.list_all(conn)]
