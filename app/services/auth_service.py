"""
認証サービスモジュール。

要件ID: RQ-FT-AUTHENTICATE-USER
設計ID: DS-CL-AUTH-SERVICE-FT-AUTHENTICATE-USER
要件概要: ログイン認証と権限制御を提供する。
設計概要: login_idでユーザーを取得し、パスワード検証と有効状態確認を行う。
呼び出し先設計ID: DS-CL-USER-REPOSITORY-DT-USER-ACCOUNT-ENTITY, DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
呼び出し元設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN
"""

from __future__ import annotations

from app.models.entities import UserAccount
from app.repositories.user_repository import UserRepository
from app.security.passwords import verify_password


class AuthService:
    """
    認証処理を提供するサービスクラス。

    要件ID: RQ-FT-AUTHENTICATE-USER
    設計ID: DS-CL-AUTH-SERVICE-FT-AUTHENTICATE-USER
    要件概要: 管理担当者と一般利用者の認証を実現する。
    設計概要: ユーザー取得、有効判定、パスワード検証を順に行い結果を返す。
    呼び出し先設計ID: DS-CL-USER-REPOSITORY-DT-USER-ACCOUNT-ENTITY, DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
    呼び出し元設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN
    """

    def __init__(self, user_repository: UserRepository) -> None:
        """
        AuthServiceを初期化する。

        Args:
            user_repository (UserRepository): ユーザーリポジトリ。

        要件ID: RQ-FT-AUTHENTICATE-USER
        設計ID: DS-CL-AUTH-SERVICE-FT-AUTHENTICATE-USER
        要件概要: 認証に必要なユーザー情報へアクセスできること。
        設計概要: リポジトリ依存を注入する。
        呼び出し先設計ID: なし
        呼び出し元設計ID: DS-MD-STREAMLIT-UI-UI-ASSET-LIST-SCREEN
        """
        self.user_repository = user_repository

    def authenticate_user(self, login_id: str, raw_password: str) -> UserAccount | None:
        """
        認証を実行する。

        Args:
            login_id (str): ログインID。
            raw_password (str): 平文パスワード。

        Returns:
            UserAccount | None: 認証成功時ユーザー情報。

        要件ID: RQ-FT-AUTHENTICATE-USER
        設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
        要件概要: ID/パスワード認証に成功したユーザーのみログインできること。
        設計概要: ユーザー存在、有効状態、パスワード一致の順で検証する。
        呼び出し先設計ID: DS-CL-USER-REPOSITORY-DT-USER-ACCOUNT-ENTITY, DS-FN-PASSWORD-HASH-NF-LOW-SECURITY-POLICY
        呼び出し元設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN
        """
        user = self.user_repository.find_by_login_id(login_id)
        if user is None:
            return None
        if not user.is_active:
            return None
        if not verify_password(raw_password, user.password_hash):
            return None
        return user
