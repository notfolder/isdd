"""
認証サービス：ログインID・パスワード検証とJWTトークン生成。

要件トレーサビリティ:
  要件ID: RQ-FT-LOGIN
  設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
  要件概要: ログインIDとパスワードで認証し、JWTトークンを発行する
  設計概要: login_id+passwordを照合し、bcryptで検証後JWTを生成して返す
  呼び出し先設計ID: DS-FN-HASH-PASSWORD-NF-SECURITY-PASSWORD, DS-FN-VERIFY-JWT-NF-SECURITY-ROLE
  呼び出し元設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.core.security import verify_password, create_jwt, verify_jwt


class AuthService:
    """
    認証サービスクラス。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOGIN
      設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
      要件概要: ログインIDとパスワードで認証し、JWTトークンを発行する
      設計概要: login_id+passwordを照合し、bcryptで検証後JWTを生成して返す
      呼び出し先設計ID: DS-FN-HASH-PASSWORD-NF-SECURITY-PASSWORD
      呼び出し元設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN
    """

    def login(self, login_id: str, password: str, db: Session) -> dict:
        """
        ログイン認証処理。

        Args:
            login_id (str): ログインID
            password (str): パスワード
            db (Session): DBセッション

        Returns:
            dict: JWTトークンと役割

        Raises:
            HTTPException: 認証失敗時に401を返す

        要件トレーサビリティ:
          要件ID: RQ-FT-LOGIN
          設計ID: DS-FN-LOGIN-FT-LOGIN
          要件概要: ログインIDとパスワードで認証し、JWTトークンを発行する
          設計概要: login_id+passwordを照合し、bcryptで検証後JWTを生成して返す
          呼び出し先設計ID: DS-FN-HASH-PASSWORD-NF-SECURITY-PASSWORD
          呼び出し元設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN
        """
        user = db.query(User).filter(User.login_id == login_id).first()
        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="認証に失敗しました",
            )
        token = create_jwt({"sub": user.login_id, "role": user.role, "user_id": user.id})
        return {"access_token": token, "role": user.role}

    def get_current_user(self, token: str, db: Session) -> User:
        """
        JWTトークンからユーザー情報を取得する。

        Args:
            token (str): JWTトークン
            db (Session): DBセッション

        Returns:
            User: ユーザーモデル

        Raises:
            HTTPException: トークン無効時に401を返す

        要件トレーサビリティ:
          要件ID: RQ-NF-SECURITY-ROLE
          設計ID: DS-FN-VERIFY-JWT-NF-SECURITY-ROLE
          要件概要: 全APIエンドポイントでBearerトークンを検証する
          設計概要: verify_jwtでペイロードを取得し、subのlogin_idでユーザーを検索する
          呼び出し先設計ID: DS-FN-VERIFY-JWT-NF-SECURITY-ROLE
          呼び出し元設計ID: DS-FN-REQUIRE-ADMIN-NF-SECURITY-ROLE
        """
        payload = verify_jwt(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="認証に失敗しました",
            )
        login_id = payload.get("sub")
        user = db.query(User).filter(User.login_id == login_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="認証に失敗しました",
            )
        return user


auth_service = AuthService()
