"""
認証APIルーターモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-LOGIN
  設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN
  要件概要: POST /api/auth/login でメール/パスワード認証を行い、JWTトークンとロールを返す。
  設計概要: FastAPIルーターでPOST /api/auth/loginエンドポイントを定義する。AuthServiceに処理を委譲する。
  呼び出し先設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
  呼び出し元設計ID: DS-MD-BACKEND-FT-LIST-EQUIPMENT
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


def login_endpoint(data: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    ログインエンドポイント。メールアドレスとパスワードで認証しJWTトークンを返す。

    Args:
        data (LoginRequest): メールアドレスとパスワード。
        db (Session): DBセッション。

    Returns:
        TokenResponse: JWTアクセストークンとロール。

    Raises:
        HTTPException: 401 認証失敗の場合。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOGIN
      設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN
      要件概要: メール/パスワード認証を行い成功時にJWTトークンを返す。失敗時は401を返す。
      設計概要: LoginRequestを受け取りAuthService.loginを呼び出す。Noneが返った場合は401を返す。
      呼び出し先設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN, DS-FN-LOGIN-FT-LOGIN
      呼び出し元設計ID: DS-MD-BACKEND-FT-LIST-EQUIPMENT
    """
    result = auth_service.login(db, data.email, data.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません",
        )
    return result


router.post("/login", response_model=TokenResponse)(login_endpoint)
