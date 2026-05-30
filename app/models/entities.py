"""
データモデル定義モジュール。

要件ID: RQ-DT-ASSET-ENTITY
設計ID: DS-SC-ASSETS-DT-ASSET-ENTITY
要件概要: 備品、ユーザー、貸出状態を業務エンティティとして管理する。
設計概要: dataclassで業務エンティティを定義し、サービスとUI間の受け渡しを明確化する。
呼び出し先設計ID: なし
呼び出し元設計ID: DS-CL-ASSET-SERVICE-FT-MANAGE-ASSET-MASTER, DS-CL-USER-SERVICE-FT-MANAGE-USER-ACCOUNT, DS-CL-LOAN-SERVICE-FT-REGISTER-LOAN
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class UserAccount:
    """
    ユーザーアカウントエンティティ。

    要件ID: RQ-DT-USER-ACCOUNT-ENTITY
    設計ID: DS-SC-USERS-DT-USER-ACCOUNT-ENTITY
    要件概要: ログインID、権限、有効状態を管理できること。
    設計概要: usersテーブルに対応するアプリ内モデルとして利用する。
    呼び出し先設計ID: なし
    呼び出し元設計ID: DS-CL-USER-REPOSITORY-DT-USER-ACCOUNT-ENTITY, DS-CL-AUTH-SERVICE-FT-AUTHENTICATE-USER
    """

    user_id: int
    display_name: str
    login_id: str
    password_hash: str
    role: str
    is_active: bool


@dataclass
class Asset:
    """
    備品エンティティ。

    要件ID: RQ-DT-ASSET-ENTITY
    設計ID: DS-SC-ASSETS-DT-ASSET-ENTITY
    要件概要: 備品台帳を管理し、状態を表示できること。
    設計概要: assetsテーブルに対応し、一覧表示と更新処理で利用する。
    呼び出し先設計ID: なし
    呼び出し元設計ID: DS-CL-ASSET-REPOSITORY-DT-ASSET-ENTITY, DS-CL-LOAN-SERVICE-FT-REGISTER-LOAN
    """

    asset_id: int
    asset_code: str
    asset_name: str
    location: str
    status: str
    version_no: int


@dataclass
class AssetStatusView:
    """
    備品一覧表示用ビューエンティティ。

    要件ID: RQ-FT-VIEW-ASSET-STATUS
    設計ID: DS-FN-VIEW-ASSET-STATUS-FT-VIEW-ASSET-STATUS
    要件概要: 備品状態と貸出中利用者を一覧で確認できること。
    設計概要: assetsとloan_statusを結合した表示専用モデルとして利用する。
    呼び出し先設計ID: なし
    呼び出し元設計ID: DS-CL-ASSET-SERVICE-FT-MANAGE-ASSET-MASTER, DS-IF-ASSET-LIST-SCREEN-UI-ASSET-LIST-SCREEN
    """

    asset_id: int
    asset_code: str
    asset_name: str
    location: str
    status: str
    borrower_name: Optional[str]
    due_date: Optional[str]
    version_no: int
