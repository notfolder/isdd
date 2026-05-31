"""
認証サービスモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-LOGIN
  設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
  要件概要: メールアドレスとパスワードで認証し、JWTトークンを返す。
  設計概要: AuthServiceクラスがパスワード検証・JWT生成を担う。メールでユーザーを検索してbcrypt照合する。
  呼び出し先設計ID: DS-FN-HASH-PASSWORD-NF-PASSWORD-HASH, DS-FN-LOGIN-FT-LOGIN
  呼び出し元設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.core.security import verify_password, create_access_token


class AuthService:
    """
    認証ビジネスロジックサービスクラス。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOGIN
      設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
      要件概要: メール/パスワード認証を行いJWTトークンを発行する。
      設計概要: ログイン処理・パスワード検証・トークン生成の3処理を担う。
      呼び出し先設計ID: DS-FN-HASH-PASSWORD-NF-PASSWORD-HASH, DS-FN-LOGIN-FT-LOGIN
      呼び出し元設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN
    """

    def login(self, db: Session, email: str, password: str) -> Optional[TokenResponse]:
        """
        メールアドレスとパスワードで認証し、成功時にTokenResponseを返す。

        Args:
            db (Session): DBセッション。
            email (str): 入力メールアドレス。
            password (str): 入力パスワード。

        Returns:
            Optional[TokenResponse]: 認証成功時はTokenResponse、失敗時はNone。

        要件トレーサビリティ:
          要件ID: RQ-FT-LOGIN
          設計ID: DS-FN-LOGIN-FT-LOGIN
          要件概要: メールとパスワードで認証する。成功時はJWTトークンとロールを返す。
          設計概要: メールでUserを検索し、bcryptでパスワード照合する。成功時はJWT生成してTokenResponseを返す。
          呼び出し先設計ID: DS-FN-HASH-PASSWORD-NF-PASSWORD-HASH, DS-SC-USER-DT-ENTITY-USER
          呼び出し元設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN
        """
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            return None
        token = create_access_token({"sub": str(user.id), "role": user.role})
        return TokenResponse(access_token=token, role=user.role)


auth_service = AuthService()
