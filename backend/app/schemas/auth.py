"""
認証スキーマ定義モジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-LOGIN
  設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN
  要件概要: メールアドレスとパスワードで認証し、JWTトークンを返す。
  設計概要: POST /api/auth/login のリクエスト・レスポンスPydanticスキーマを定義する。
  呼び出し先設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
  呼び出し元設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN
"""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """
    ログインリクエストスキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOGIN
      設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN
      要件概要: メールアドレスとパスワードを受け取り認証を行う。
      設計概要: email・passwordの2フィールドを持つリクエストスキーマ。
      呼び出し先設計ID: DS-FN-LOGIN-FT-LOGIN
      呼び出し元設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN
    """

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """
    ログイン成功時のレスポンススキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOGIN
      設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN
      要件概要: 認証成功後にJWTアクセストークンとロールを返す。
      設計概要: access_token・token_type・roleを持つレスポンススキーマ。
      呼び出し先設計ID: なし
      呼び出し元設計ID: DS-FN-LOGIN-FT-LOGIN
    """

    access_token: str
    token_type: str = "bearer"
    role: str
