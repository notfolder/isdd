"""
認証APIルーターモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-LOGIN
  設計ID: DS-CL-AUTH-ROUTER-FT-LOGIN
  要件概要: ログイン・ログアウトAPIエンドポイントを提供する。JWTをHTTP-only Cookieで管理する。
  設計概要: FastAPI Router で /api/auth/login と /api/auth/logout を定義する。
  呼び出し先: DS-CL-AUTH-SERVICE-FT-LOGIN
  呼び出し元: DS-MD-BACKEND-FT-MANAGE-EQUIPMENT
"""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """
    ログインリクエストスキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOGIN
      設計ID: DS-CL-AUTH-ROUTER-FT-LOGIN
      要件概要: ログインIDとパスワードを受け取ってログインする。
      設計概要: Pydantic BaseModel でリクエストボディを定義する。
      呼び出し先: なし
      呼び出し元: DS-CL-AUTH-ROUTER-FT-LOGIN
    """
    login_id: str
    password: str


@router.post("/login")
def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """
    ログインエンドポイント。認証成功時にJWTをHTTP-only Cookieにセットする。

    Args:
        request (LoginRequest): ログインIDとパスワード。
        response (Response): FastAPI レスポンスオブジェクト（Cookie設定に使用）。
        db (Session): DBセッション。

    Returns:
        dict: ログインIDと表示名とロールを含むレスポンス。

    Raises:
        HTTPException: 401 - 認証失敗の場合。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOGIN, RQ-NF-SESSION-AUTO-LOGOUT-60MIN
      設計ID: DS-CL-AUTH-ROUTER-FT-LOGIN
      要件概要: ログインIDとパスワードで認証し、成功時に60分有効なJWTをHTTP-only Cookieで返す。
      設計概要: AuthService.authenticate で認証後、JWT を set_cookie で HTTP-only SameSite=Strict に設定する。
      呼び出し先: DS-CL-AUTH-SERVICE-FT-LOGIN
      呼び出し元: フロントエンド DS-IF-AUTH-API-FT-LOGIN
    """
    service = AuthService(db)
    user = service.authenticate(request.login_id, request.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ログインIDまたはパスワードが正しくありません",
        )
    token = service.create_token(user)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="strict",
        max_age=3600,
    )
    return {"login_id": user.login_id, "display_name": user.display_name, "role": user.role}


@router.post("/logout")
def logout(response: Response):
    """
    ログアウトエンドポイント。JWTクッキーを削除する。

    Args:
        response (Response): FastAPI レスポンスオブジェクト（Cookie削除に使用）。

    Returns:
        dict: ログアウト完了メッセージ。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOGIN
      設計ID: DS-CL-AUTH-ROUTER-FT-LOGIN
      要件概要: ログアウト時にセッションを終了し、Cookieを削除する。
      設計概要: delete_cookie で access_token Cookie を削除してセッションを無効化する。
      呼び出し先: なし
      呼び出し元: フロントエンド DS-IF-AUTH-API-FT-LOGIN
    """
    response.delete_cookie(key="access_token", samesite="strict")
    return {"message": "ログアウトしました"}
