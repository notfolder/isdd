"""
FastAPI依存性注入モジュール（認証・認可）。

要件トレーサビリティ:
  要件ID: RQ-NF-ROLE-CONTROL
  設計ID: DS-IF-ROLE-MIDDLEWARE-NF-ROLE-CONTROL
  要件概要: 管理者/一般の権限制御をページ単位で行う。管理者専用エンドポイントへの一般ユーザーアクセスを禁止する。
  設計概要: FastAPI Dependsで認証済みユーザー取得とロール確認を行う依存関数を提供する。
  呼び出し先設計ID: DS-FN-CHECK-ROLE-NF-ROLE-CONTROL, DS-SC-USER-DT-ENTITY-USER
  呼び出し元設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT, DS-IF-MANAGE-USERS-FT-MANAGE-USERS
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import decode_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    JWTトークンから認証済みユーザーを取得する。

    Args:
        token (str): BearerトークンをOAuth2スキームで取得。
        db (Session): DBセッション。

    Returns:
        User: 認証済みUserモデルインスタンス。

    Raises:
        HTTPException: 401 トークン無効・ユーザー不在の場合。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOGIN
      設計ID: DS-FN-CHECK-ROLE-NF-ROLE-CONTROL
      要件概要: 認証済みユーザーのみがアプリにアクセスできる。未認証は401を返す。
      設計概要: JWTデコードでsubクレームを取得しDBからユーザーを検索する。無効時は401 Unauthorized。
      呼び出し先設計ID: DS-FN-CHECK-ROLE-NF-ROLE-CONTROL, DS-SC-USER-DT-ENTITY-USER
      呼び出し元設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT, DS-IF-LIST-USERS-FT-MANAGE-USERS
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証が必要です",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    管理者ロールを要求するDependency。

    Args:
        current_user (User): get_current_userで取得した認証済みユーザー。

    Returns:
        User: 管理者ユーザー。

    Raises:
        HTTPException: 403 管理者以外のアクセス。

    要件トレーサビリティ:
      要件ID: RQ-NF-ROLE-CONTROL
      設計ID: DS-FN-CHECK-ROLE-NF-ROLE-CONTROL
      要件概要: 管理者/一般の権限制御をページ単位で行う。管理者専用操作への一般ユーザーアクセスを禁止する。
      設計概要: current_user.roleがadminでない場合は403 Forbiddenを返す。
      呼び出し先設計ID: なし
      呼び出し元設計ID: DS-IF-CREATE-EQUIPMENT-FT-CREATE-EQUIPMENT, DS-IF-RECORD-LENDING-FT-RECORD-LENDING, DS-IF-MANAGE-USERS-FT-MANAGE-USERS
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者権限が必要です",
        )
    return current_user
