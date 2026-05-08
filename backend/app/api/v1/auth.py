"""
認証エンドポイント：ログイン・ログアウト。

要件トレーサビリティ:
  要件ID: RQ-FT-LOGIN, RQ-FT-LOGOUT
  設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN, DS-IF-AUTH-LOGOUT-FT-LOGOUT
  要件概要: ログインIDとパスワードで認証しJWTトークンを返す。ログアウトはフロントエンド側でトークン削除する
  設計概要: POST /api/auth/login(TokenResponseを返す)、POST /api/auth/logout(200 OKを返すのみ)を実装する
  呼び出し先設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
  呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.services.auth_service import auth_service

router = APIRouter()


class LoginRequest(BaseModel):
    """
    ログインリクエストスキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOGIN
      設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN
      要件概要: ログインIDとパスワードを受け取る
      設計概要: login_idとpasswordを必須フィールドとして定義する
      呼び出し先設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
      呼び出し元設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN
    """

    login_id: str
    password: str


@router.post("/auth/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    ログイン認証エンドポイント。

    Args:
        request (LoginRequest): ログインリクエスト
        db (Session): DBセッション

    Returns:
        dict: JWTトークンと役割

    要件トレーサビリティ:
      要件ID: RQ-FT-LOGIN
      設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN
      要件概要: ログインIDとパスワードで認証し、JWTトークンを発行する
      設計概要: POST /api/auth/loginでAuthService.loginを呼び出しTokenResponseを返す
      呼び出し先設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
      呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
    """
    return auth_service.login(request.login_id, request.password, db)


@router.post("/auth/logout")
def logout():
    """
    ログアウトエンドポイント（フロントエンド側でトークン削除するため200 OKを返すのみ）。

    Returns:
        dict: 成功メッセージ

    要件トレーサビリティ:
      要件ID: RQ-FT-LOGOUT
      設計ID: DS-IF-AUTH-LOGOUT-FT-LOGOUT
      要件概要: セッションを終了し他者が継続操作できないようにする
      設計概要: POST /api/auth/logoutで200 OKを返す。トークン削除はフロントエンド側で実行
      呼び出し先設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
      呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
    """
    return {"message": "ログアウトしました"}
