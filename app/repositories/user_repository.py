"""
ユーザーリポジトリモジュール。

要件ID: RQ-DT-USER-ACCOUNT-ENTITY
設計ID: DS-CL-USER-REPOSITORY-DT-USER-ACCOUNT-ENTITY
要件概要: ユーザーアカウントの登録、更新、有効状態管理が必要である。
設計概要: usersテーブルのCRUDを提供し、認証とユーザー管理から利用される。
呼び出し先設計ID: DS-SC-USERS-DT-USER-ACCOUNT-ENTITY
呼び出し元設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USER-ACCOUNT, DS-CL-AUTH-SERVICE-FT-AUTHENTICATE-USER
"""

from __future__ import annotations

from sqlite3 import Connection
from typing import Optional

from app.models.entities import UserAccount


class UserRepository:
    """
    usersテーブルのデータアクセスを提供するクラス。

    要件ID: RQ-DT-USER-ACCOUNT-ENTITY
    設計ID: DS-CL-USER-REPOSITORY-DT-USER-ACCOUNT-ENTITY
    要件概要: ユーザー情報を永続管理し、認証と権限制御に使えること。
    設計概要: usersテーブルに対する検索・登録・更新処理を集約する。
    呼び出し先設計ID: DS-SC-USERS-DT-USER-ACCOUNT-ENTITY
    呼び出し元設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USER-ACCOUNT, DS-CL-AUTH-SERVICE-FT-AUTHENTICATE-USER
    """

    def __init__(self, conn: Connection) -> None:
        """
        リポジトリを初期化する。

        Args:
            conn (Connection): SQLite接続。

        要件ID: RQ-DT-USER-ACCOUNT-ENTITY
        設計ID: DS-CL-USER-REPOSITORY-DT-USER-ACCOUNT-ENTITY
        要件概要: ユーザーアカウント情報を継続的に参照・更新できること。
        設計概要: 接続を保持して各メソッドで利用する。
        呼び出し先設計ID: なし
        呼び出し元設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USER-ACCOUNT, DS-CL-AUTH-SERVICE-FT-AUTHENTICATE-USER
        """
        self.conn = conn

    def find_by_login_id(self, login_id: str) -> Optional[UserAccount]:
        """
        ログインIDでユーザーを検索する。

        Args:
            login_id (str): ログインID。

        Returns:
            Optional[UserAccount]: 見つかったユーザー。存在しない場合はNone。

        要件ID: RQ-FT-AUTHENTICATE-USER
        設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
        要件概要: ログイン時にID/パスワードを検証し、権限判定を行う。
        設計概要: ログインIDに一致するユーザーを取得して認証処理へ渡す。
        呼び出し先設計ID: DS-SC-USERS-DT-USER-ACCOUNT-ENTITY
        呼び出し元設計ID: DS-CL-AUTH-SERVICE-FT-AUTHENTICATE-USER
        """
        row = self.conn.execute(
            """
            SELECT user_id, display_name, login_id, password_hash, role, is_active
            FROM users
            WHERE login_id = ?
            """,
            (login_id,),
        ).fetchone()
        if not row:
            return None
        return UserAccount(
            user_id=row["user_id"],
            display_name=row["display_name"],
            login_id=row["login_id"],
            password_hash=row["password_hash"],
            role=row["role"],
            is_active=bool(row["is_active"]),
        )

    def list_all(self) -> list[UserAccount]:
        """
        全ユーザーを一覧で取得する。

        Returns:
            list[UserAccount]: ユーザー一覧。

        要件ID: RQ-FT-MANAGE-USER-ACCOUNT
        設計ID: DS-FN-MANAGE-USER-ACCOUNT-FT-MANAGE-USER-ACCOUNT
        要件概要: ユーザーアカウントの一覧確認と管理ができること。
        設計概要: ユーザー管理画面表示のためにusersを全件取得する。
        呼び出し先設計ID: DS-SC-USERS-DT-USER-ACCOUNT-ENTITY
        呼び出し元設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USER-ACCOUNT
        """
        rows = self.conn.execute(
            """
            SELECT user_id, display_name, login_id, password_hash, role, is_active
            FROM users
            ORDER BY user_id
            """
        ).fetchall()
        return [
            UserAccount(
                user_id=row["user_id"],
                display_name=row["display_name"],
                login_id=row["login_id"],
                password_hash=row["password_hash"],
                role=row["role"],
                is_active=bool(row["is_active"]),
            )
            for row in rows
        ]

    def save(self, user: UserAccount) -> None:
        """
        ユーザー情報を登録または更新する。

        Args:
            user (UserAccount): 保存対象ユーザー。

        要件ID: RQ-FT-MANAGE-USER-ACCOUNT
        設計ID: DS-FN-MANAGE-USER-ACCOUNT-FT-MANAGE-USER-ACCOUNT
        要件概要: ユーザー登録、編集、有効/無効の管理を実現する。
        設計概要: user_idの有無でINSERT/UPDATEを切り替えて保存する。
        呼び出し先設計ID: DS-SC-USERS-DT-USER-ACCOUNT-ENTITY
        呼び出し元設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USER-ACCOUNT
        """
        if user.user_id == 0:
            self.conn.execute(
                """
                INSERT INTO users (display_name, login_id, password_hash, role, is_active)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user.display_name,
                    user.login_id,
                    user.password_hash,
                    user.role,
                    int(user.is_active),
                ),
            )
        else:
            self.conn.execute(
                """
                UPDATE users
                SET display_name = ?, login_id = ?, password_hash = ?, role = ?, is_active = ?
                WHERE user_id = ?
                """,
                (
                    user.display_name,
                    user.login_id,
                    user.password_hash,
                    user.role,
                    int(user.is_active),
                    user.user_id,
                ),
            )
        self.conn.commit()
