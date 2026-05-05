"""
JWT 生成・検証・認証依存関数モジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-LOGIN, RQ-NF-ROLE-ACCESS, RQ-NF-SESSION-AUTO-LOGOUT-60MIN
  設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
  要件概要: JWT を HTTP-only Cookie で管理し、ロールに応じた認可制御を行う。60分で自動失効する。
  設計概要: jose ライブラリで JWT を HS256 で生成・検証する。get_current_user / require_admin を Depends として提供する。
  呼び出し先: DS-MD-DATABASE-DT-EQUIPMENT-ENTITY
  呼び出し元: DS-CL-AUTH-ROUTER-FT-LOGIN, DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT, DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Cookie
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(data: dict) -> str:
    """
    JWT アクセストークンを生成する。

    Args:
        data (dict): トークンに含めるペイロード（sub: login_id, role を含む）。

    Returns:
        str: 署名済み JWT 文字列。有効期限は60分。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOGIN, RQ-NF-SESSION-AUTO-LOGOUT-60MIN
      設計ID: DS-FN-AUTH-JWT-FT-LOGIN
      要件概要: ログイン成功時に60分有効な JWT を発行する。
      設計概要: HS256 で署名し、exp クレームに60分後の UTC 時刻を設定する。
      呼び出し先: なし
      呼び出し元: DS-CL-AUTH-SERVICE-FT-LOGIN
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """
    JWT トークンを検証してペイロードを返す。

    Args:
        token (str): 検証する JWT 文字列。

    Returns:
        Optional[dict]: 有効なトークンの場合はペイロード dict、無効な場合は None。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOGIN
      設計ID: DS-FN-AUTH-JWT-FT-LOGIN
      要件概要: Cookie の JWT を検証してユーザー情報を取得する。
      設計概要: jose.jwt.decode で署名と有効期限を検証する。例外時は None を返す。
      呼び出し先: なし
      呼び出し元: DS-CL-AUTH-SERVICE-FT-LOGIN
    """
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None


def get_current_user(
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    """
    ログイン済みユーザーを取得する Depends 関数。

    Args:
        access_token (Optional[str]): HTTP-only Cookie の JWT。
        db (Session): DBセッション。

    Returns:
        User: 認証済みユーザーモデル。

    Raises:
        HTTPException: 401 - Cookie なし、トークン無効、ユーザー不存在の場合。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOGIN, RQ-NF-ROLE-ACCESS
      設計ID: DS-FN-ROLE-CHECK-NF-ROLE-BASED-AUTHORIZATION
      要件概要: 全認証が必要な API エンドポイントでログイン状態を確認する。
      設計概要: Cookie の JWT を検証し、login_id でユーザーを検索して返す。
      呼び出し先: DS-MD-DATABASE-DT-EQUIPMENT-ENTITY
      呼び出し元: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT, DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証が必要です",
    )
    if not access_token:
        raise credentials_exception
    payload = decode_token(access_token)
    if payload is None:
        raise credentials_exception
    login_id: str = payload.get("sub")
    if login_id is None:
        raise credentials_exception
    user = db.query(User).filter(User.login_id == login_id).first()
    if user is None:
        raise credentials_exception
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    管理者権限を要求する Depends 関数。

    Args:
        current_user (User): get_current_user で取得したユーザー。

    Returns:
        User: 管理者ロールのユーザー。

    Raises:
        HTTPException: 403 - 管理者以外のユーザーの場合。

    要件トレーサビリティ:
      要件ID: RQ-NF-ROLE-ACCESS
      設計ID: DS-FN-ROLE-CHECK-NF-ROLE-BASED-AUTHORIZATION
      要件概要: 管理者専用操作（備品CRUD・貸出・返却・利用者管理）は管理者のみ実行可能にする。
      設計概要: get_current_user で取得したユーザーの role を確認し、admin 以外は 403 を返す。
      呼び出し先: DS-CL-AUTH-SERVICE-FT-LOGIN
      呼び出し元: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT, DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です",
        )
    return current_user
