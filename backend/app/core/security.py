"""
JWT生成・検証とbcryptパスワードハッシュのセキュリティヘルパー。

要件トレーサビリティ:
  要件ID: RQ-NF-SECURITY-PASSWORD, RQ-NF-SECURITY-ROLE
  設計ID: DS-FN-HASH-PASSWORD-NF-SECURITY-PASSWORD, DS-FN-VERIFY-JWT-NF-SECURITY-ROLE
  要件概要: パスワードをbcryptでハッシュ化して保存し、JWTで認証状態を管理する
  設計概要: passlibのbcryptでハッシュ化・検証、python-joseでJWT生成・検証を実装する
  呼び出し先設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
  呼び出し元設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN, DS-CL-USER-SERVICE-FT-CREATE-USER
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = "equipment-management-secret-key-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    パスワードをbcryptでハッシュ化する。

    Args:
        plain_password (str): 平文パスワード

    Returns:
        str: bcryptハッシュ

    要件トレーサビリティ:
      要件ID: RQ-NF-SECURITY-PASSWORD
      設計ID: DS-FN-HASH-PASSWORD-NF-SECURITY-PASSWORD
      要件概要: パスワードをハッシュ化してDBに保存する
      設計概要: passlibのbcryptでハッシュ化し平文保存を禁止する
      呼び出し先設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
      呼び出し元設計ID: DS-CL-USER-SERVICE-FT-CREATE-USER, DS-FN-SEED-INITIAL-USER-FT-CREATE-USER
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    平文パスワードとbcryptハッシュを照合する。

    Args:
        plain_password (str): 平文パスワード
        hashed_password (str): bcryptハッシュ

    Returns:
        bool: 照合成功ならTrue

    要件トレーサビリティ:
      要件ID: RQ-NF-SECURITY-PASSWORD
      設計ID: DS-FN-HASH-PASSWORD-NF-SECURITY-PASSWORD
      要件概要: パスワードをハッシュ化してDBに保存する
      設計概要: passlibのbcrypt.verifyで照合する
      呼び出し先設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
      呼び出し元設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_jwt(payload: dict) -> str:
    """
    JWTアクセストークンを生成する。

    Args:
        payload (dict): JWTペイロード（subにlogin_id、roleを含む）

    Returns:
        str: JWTトークン文字列

    要件トレーサビリティ:
      要件ID: RQ-NF-SECURITY-ROLE
      設計ID: DS-FN-VERIFY-JWT-NF-SECURITY-ROLE
      要件概要: JWTで認証状態を管理し役割ベースアクセス制御を実装する
      設計概要: python-joseでHS256署名のJWTを生成し有効期限を8時間に設定する
      呼び出し先設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
      呼び出し元設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
    """
    to_encode = payload.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_jwt(token: str) -> Optional[dict]:
    """
    JWTトークンを検証してペイロードを返す。

    Args:
        token (str): JWTトークン文字列

    Returns:
        Optional[dict]: 検証成功時はペイロード、失敗時はNone

    要件トレーサビリティ:
      要件ID: RQ-NF-SECURITY-ROLE
      設計ID: DS-FN-VERIFY-JWT-NF-SECURITY-ROLE
      要件概要: 全APIエンドポイントでBearerトークンを検証する
      設計概要: python-joseでJWTを検証し有効期限切れ・署名不正の場合はNoneを返す
      呼び出し先設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
      呼び出し元設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN, DS-FN-REQUIRE-ADMIN-NF-SECURITY-ROLE
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
