"""
ユーザースキーマ定義モジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-MANAGE-USERS
  設計ID: DS-IF-LIST-USERS-FT-MANAGE-USERS
  要件概要: ユーザーCRUDのリクエスト・レスポンスを定義する。社員マスターとユーザーアカウントを一本化。
  設計概要: ユーザー管理APIのPydanticスキーマ。パスワードは作成時のみ必須、更新時はオプション。
  呼び出し先設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USERS
  呼び出し元設計ID: DS-IF-LIST-USERS-FT-MANAGE-USERS
"""

from typing import Optional, Literal
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """
    ユーザー登録リクエストスキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-USERS
      設計ID: DS-IF-CREATE-USER-FT-MANAGE-USERS
      要件概要: 氏名・メールアドレス・パスワード・権限を受け取りユーザーを登録する。
      設計概要: name・email・password・roleの4フィールドを持つ登録リクエストスキーマ。
      呼び出し先設計ID: DS-FN-CREATE-USER-FT-MANAGE-USERS
      呼び出し元設計ID: DS-IF-CREATE-USER-FT-MANAGE-USERS
    """

    name: str
    email: EmailStr
    password: str
    role: Literal["admin", "general"] = "general"


class UserUpdate(BaseModel):
    """
    ユーザー更新リクエストスキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-USERS
      設計ID: DS-IF-UPDATE-USER-FT-MANAGE-USERS
      要件概要: 氏名・メール・パスワード・権限を更新する。パスワードは変更時のみ指定。
      設計概要: name・email・password（オプション）・roleの4フィールド。passwordはNone時は更新しない。
      呼び出し先設計ID: DS-FN-UPDATE-USER-FT-MANAGE-USERS
      呼び出し元設計ID: DS-IF-UPDATE-USER-FT-MANAGE-USERS
    """

    name: str
    email: EmailStr
    password: Optional[str] = None
    role: Literal["admin", "general"] = "general"


class UserResponse(BaseModel):
    """
    ユーザーレスポンススキーマ（パスワード除外）。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-USERS
      設計ID: DS-IF-LIST-USERS-FT-MANAGE-USERS
      要件概要: ユーザー一覧で氏名・メールアドレス・権限を返す。パスワードは含めない。
      設計概要: id・name・email・roleを持つレスポンス。password_hashは含めない。
      呼び出し先設計ID: なし
      呼び出し元設計ID: DS-FN-MANAGE-USERS-FT-MANAGE-USERS
    """

    id: int
    name: str
    email: str
    role: str

    model_config = {"from_attributes": True}
