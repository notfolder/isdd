"""
セキュリティユーティリティモジュール（JWT・パスワードハッシュ）。

要件トレーサビリティ:
  要件ID: RQ-NF-PASSWORD-HASH
  設計ID: DS-FN-HASH-PASSWORD-NF-PASSWORD-HASH
  要件概要: パスワードはbcryptでハッシュ化して保存する。平文パスワードをDBに保存しない。
  設計概要: passlib[bcrypt]でパスワードハッシュ化・検証を行う。JWTはHS256で生成し有効期限8時間とする。
  呼び出し先設計ID: なし
  呼び出し元設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN, DS-CL-USER-SERVICE-FT-MANAGE-USERS
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("SECRET_KEY", "changeme-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    平文パスワードとハッシュを照合する。

    Args:
        plain_password (str): 入力されたパスワード。
        hashed_password (str): DB保存済みのbcryptハッシュ。

    Returns:
        bool: 一致すればTrue。

    要件トレーサビリティ:
      要件ID: RQ-NF-PASSWORD-HASH
      設計ID: DS-FN-HASH-PASSWORD-NF-PASSWORD-HASH
      要件概要: パスワードはbcryptでハッシュ化して保存する。認証時はハッシュ照合を行う。
      設計概要: passlib CryptContextのverifyメソッドでbcrypt照合を行う。
      呼び出し先設計ID: なし
      呼び出し元設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """
    パスワードをbcryptでハッシュ化する。

    Args:
        password (str): 平文パスワード。

    Returns:
        str: bcryptハッシュ文字列。

    要件トレーサビリティ:
      要件ID: RQ-NF-PASSWORD-HASH
      設計ID: DS-FN-HASH-PASSWORD-NF-PASSWORD-HASH
      要件概要: パスワードはbcryptでハッシュ化して保存する。
      設計概要: passlib CryptContextのhashメソッドでbcryptハッシュを生成する。
      呼び出し先設計ID: なし
      呼び出し元設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USERS, DS-CL-AUTH-SERVICE-FT-LOGIN
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWTアクセストークンを生成する。

    Args:
        data (dict): トークンに埋め込むクレーム（sub, role等）。
        expires_delta (Optional[timedelta]): 有効期限の差分。省略時は8時間。

    Returns:
        str: エンコードされたJWTトークン。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOGIN
      設計ID: DS-FN-LOGIN-FT-LOGIN
      要件概要: 認証成功時にJWTトークンを生成して返す。
      設計概要: HS256アルゴリズムで有効期限8時間のJWTを生成する。dataにexpクレームを追加してエンコード。
      呼び出し先設計ID: なし
      呼び出し元設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """
    JWTトークンをデコードしてクレームを返す。

    Args:
        token (str): Bearerトークン文字列。

    Returns:
        Optional[dict]: クレーム辞書。無効時はNone。

    要件トレーサビリティ:
      要件ID: RQ-NF-ROLE-CONTROL
      設計ID: DS-FN-CHECK-ROLE-NF-ROLE-CONTROL
      要件概要: 管理者/一般の権限制御をページ単位で行う。JWTからロールを取得して認可する。
      設計概要: JWTをデコードし、ロールを含むクレームを返す。JWTErrorが発生した場合はNoneを返す。
      呼び出し先設計ID: なし
      呼び出し元設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN, DS-IF-ROLE-MIDDLEWARE-NF-ROLE-CONTROL
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
