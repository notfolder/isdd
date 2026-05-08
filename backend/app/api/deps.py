"""
FastAPI依存注入：JWT認証チェックと管理者ロール確認。

要件トレーサビリティ:
  要件ID: RQ-NF-SECURITY-ROLE
  設計ID: DS-FN-REQUIRE-ADMIN-NF-SECURITY-ROLE
  要件概要: 管理者と一般ユーザーのロールベースアクセス制御を実装する
  設計概要: get_current_user(JWT検証)とrequire_admin(roleチェック)をFastAPI依存注入として実装する
  呼び出し先設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
  呼び出し元設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT, DS-IF-CREATE-EQUIPMENT-FT-CREATE-EQUIPMENT
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.services.auth_service import auth_service

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    現在のユーザーをJWTトークンから取得する依存注入関数。

    Args:
        credentials (HTTPAuthorizationCredentials): Bearer認証情報
        db (Session): DBセッション

    Returns:
        User: 認証済みユーザー

    Raises:
        HTTPException: トークン無効時に401を返す

    要件トレーサビリティ:
      要件ID: RQ-NF-SECURITY-ROLE
      設計ID: DS-FN-VERIFY-JWT-NF-SECURITY-ROLE
      要件概要: 全APIエンドポイントでBearerトークンを検証する
      設計概要: HTTPBearerでトークンを抽出し、AuthServiceでユーザーを取得する
      呼び出し先設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
      呼び出し元設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
    """
    return auth_service.get_current_user(credentials.credentials, db)


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    管理者ロールを必須とする依存注入関数。

    Args:
        current_user (User): 現在のユーザー

    Returns:
        User: 管理者ユーザー

    Raises:
        HTTPException: 管理者以外のアクセスは403を返す

    要件トレーサビリティ:
      要件ID: RQ-NF-SECURITY-ROLE
      設計ID: DS-FN-REQUIRE-ADMIN-NF-SECURITY-ROLE
      要件概要: 管理者専用エンドポイントへのアクセスを制御する
      設計概要: roleがadminでない場合は403 Forbiddenを返す
      呼び出し先設計ID: DS-FN-VERIFY-JWT-NF-SECURITY-ROLE
      呼び出し元設計ID: DS-IF-CREATE-EQUIPMENT-FT-CREATE-EQUIPMENT, DS-IF-DELETE-EQUIPMENT-FT-DELETE-EQUIPMENT
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です",
        )
    return current_user
