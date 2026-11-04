"""パスワードのハッシュと照合、セッショントークンの作成。"""

import hashlib
import hmac
import secrets

PBKDF2_ITERATIONS = 200_000
SCHEME = "pbkdf2_sha256"


def hash_password(password: str) -> str:
    """パスワードを PBKDF2-HMAC-SHA256 でハッシュにする。

    Args:
        password: 平文のパスワード。

    Returns:
        `方式$反復回数$ソルト(16進)$ハッシュ(16進)` の形の文字列。
    """
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"{SCHEME}${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """平文のパスワードが保存済みのハッシュと一致するかを返す。

    Args:
        password: 入力されたパスワード。
        stored: 保存済みのハッシュ文字列。

    Returns:
        一致すれば True。形式が壊れていれば False。
    """
    parts = stored.split("$")
    if len(parts) != 4 or parts[0] != SCHEME:
        return False
    try:
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(digest.hex(), parts[3])


def new_session_token() -> str:
    """推測されない十分な長さのセッショントークンを返す。

    Returns:
        URL に使える文字だけの 43 文字程度の文字列。
    """
    return secrets.token_urlsafe(32)
