"""
認証サービスモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-LOGIN, RQ-NF-PASSWORD-HASH
  設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
  要件概要: ログインIDとパスワードでユーザーを認証し、JWTトークンを発行する。
  設計概要: bcrypt でパスワードを検証し、認証成功時に JWT を生成して返す。
  呼び出し先: DS-CL-USER-REPO-DT-BORROWER-ENTITY, DS-FN-AUTH-JWT-FT-LOGIN
  呼び出し元: DS-CL-AUTH-ROUTER-FT-LOGIN
"""
from typing import Optional
import bcrypt
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.auth import create_access_token


class AuthService:
    """
    認証処理を担うサービスクラス。

    Args:
        db (Session): SQLAlchemy セッション。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOGIN, RQ-NF-PASSWORD-HASH
      設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
      要件概要: ログインIDとパスワードを検証してJWTを発行する。
      設計概要: UserRepository を直接使わず db.query で認証し、JWT 生成は create_access_token に委譲する。
      呼び出し先: DS-FN-AUTH-JWT-FT-LOGIN
      呼び出し元: DS-CL-AUTH-ROUTER-FT-LOGIN
    """

    def __init__(self, db: Session):
        self.db = db

    def authenticate(self, login_id: str, password: str) -> Optional[User]:
        """
        ログインIDとパスワードでユーザーを認証する。

        Args:
            login_id (str): 入力されたログインID。
            password (str): 入力された平文パスワード。

        Returns:
            Optional[User]: 認証成功時はユーザーモデル、失敗時は None。

        要件トレーサビリティ:
          要件ID: RQ-FT-LOGIN, RQ-NF-PASSWORD-HASH
          設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
          要件概要: ログインID・パスワードが一致する場合のみ認証を成功させる。パスワードは bcrypt で検証する。
          設計概要: login_id でユーザーを検索し、bcrypt.checkpw でパスワードを照合する。不一致は None を返す。
          呼び出し先: DS-MD-USER-DT-BORROWER-ENTITY
          呼び出し元: DS-CL-AUTH-ROUTER-FT-LOGIN
        """
        user = self.db.query(User).filter(User.login_id == login_id).first()
        if user is None:
            return None
        if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            return None
        return user

    def create_token(self, user: User) -> str:
        """
        認証済みユーザーのJWTトークンを生成する。

        Args:
            user (User): 認証済みユーザーモデル。

        Returns:
            str: 署名済みJWT文字列。

        要件トレーサビリティ:
          要件ID: RQ-FT-LOGIN, RQ-NF-SESSION-AUTO-LOGOUT-60MIN
          設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
          要件概要: 認証成功後に60分有効なJWTを発行し、ロール情報をペイロードに含める。
          設計概要: create_access_token に sub(login_id) と role を渡してトークンを生成する。
          呼び出し先: DS-FN-AUTH-JWT-FT-LOGIN
          呼び出し元: DS-CL-AUTH-ROUTER-FT-LOGIN
        """
        return create_access_token({"sub": user.login_id, "role": user.role})
