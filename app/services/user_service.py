"""
ユーザーサービスモジュール。

要件ID: RQ-FT-MANAGE-USER-ACCOUNT
設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USER-ACCOUNT
要件概要: ユーザーの登録、編集、有効無効管理を提供する。
設計概要: 重複ログインIDを検証し、パスワードをハッシュ化して保存する。
呼び出し先設計ID: DS-CL-USER-REPOSITORY-DT-USER-ACCOUNT-ENTITY, DS-FN-ERR-USER-DUPLICATE-FT-MANAGE-USER-ACCOUNT
呼び出し元設計ID: DS-IF-USER-ENTRY-POPUP-FT-MANAGE-USER-ACCOUNT
"""

from __future__ import annotations

from app.models.entities import UserAccount
from app.repositories.user_repository import UserRepository
from app.security.passwords import hash_password


class UserService:
    """
    ユーザー管理処理を提供するサービスクラス。

    要件ID: RQ-FT-MANAGE-USER-ACCOUNT
    設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USER-ACCOUNT
    要件概要: ユーザー登録と編集を管理担当者が行えること。
    設計概要: 入力値を検証し、必要に応じてハッシュ化して保存する。
    呼び出し先設計ID: DS-CL-USER-REPOSITORY-DT-USER-ACCOUNT-ENTITY, DS-FN-PASSWORD-HASH-NF-LOW-SECURITY-POLICY
    呼び出し元設計ID: DS-IF-USER-ENTRY-POPUP-FT-MANAGE-USER-ACCOUNT
    """

    def __init__(self, user_repository: UserRepository) -> None:
        """
        UserServiceを初期化する。

        Args:
            user_repository (UserRepository): ユーザーリポジトリ。

        要件ID: RQ-FT-MANAGE-USER-ACCOUNT
        設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USER-ACCOUNT
        要件概要: ユーザー管理処理を一貫して実行できること。
        設計概要: リポジトリ依存を注入する。
        呼び出し先設計ID: なし
        呼び出し元設計ID: DS-MD-STREAMLIT-UI-UI-ASSET-LIST-SCREEN
        """
        self.user_repository = user_repository

    def list_users(self) -> list[UserAccount]:
        """
        ユーザー一覧を返す。

        Returns:
            list[UserAccount]: ユーザー一覧。

        要件ID: RQ-FT-MANAGE-USER-ACCOUNT
        設計ID: DS-FN-MANAGE-USER-ACCOUNT-FT-MANAGE-USER-ACCOUNT
        要件概要: ユーザー管理画面でアカウント一覧を確認できること。
        設計概要: リポジトリから一覧を取得する。
        呼び出し先設計ID: DS-CL-USER-REPOSITORY-DT-USER-ACCOUNT-ENTITY
        呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
        """
        return self.user_repository.list_all()

    def save_user_account(
        self,
        user_id: int,
        display_name: str,
        login_id: str,
        raw_password: str,
        role: str,
        is_active: bool,
    ) -> tuple[bool, str]:
        """
        ユーザーを登録または更新する。

        Args:
            user_id (int): ユーザーID。
            display_name (str): 氏名。
            login_id (str): ログインID。
            raw_password (str): パスワード。
            role (str): 権限。
            is_active (bool): 有効状態。

        Returns:
            tuple[bool, str]: 成否とメッセージ。

        要件ID: RQ-FT-MANAGE-USER-ACCOUNT
        設計ID: DS-FN-MANAGE-USER-ACCOUNT-FT-MANAGE-USER-ACCOUNT
        要件概要: ユーザー登録/編集を実行し、重複IDを拒否すること。
        設計概要: login_id重複を確認し、問題なければ保存する。
        呼び出し先設計ID: DS-FN-ERR-USER-DUPLICATE-FT-MANAGE-USER-ACCOUNT, DS-CL-USER-REPOSITORY-DT-USER-ACCOUNT-ENTITY, DS-FN-PASSWORD-HASH-NF-LOW-SECURITY-POLICY
        呼び出し元設計ID: DS-IF-USER-ENTRY-POPUP-FT-MANAGE-USER-ACCOUNT
        """
        if not display_name or not login_id or not role:
            return False, "氏名、ログインID、権限は必須です。"

        existing = self.user_repository.find_by_login_id(login_id)
        if existing and existing.user_id != user_id:
            return False, "ログインIDが重複しています。"

        password_hash = existing.password_hash if existing else ""
        if raw_password:
            password_hash = hash_password(raw_password)
        if not password_hash:
            return False, "パスワードは必須です。"

        self.user_repository.save(
            UserAccount(
                user_id=user_id,
                display_name=display_name,
                login_id=login_id,
                password_hash=password_hash,
                role=role,
                is_active=is_active,
            )
        )
        return True, "ユーザーを保存しました。"
