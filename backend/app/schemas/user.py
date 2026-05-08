"""
ユーザーのPydanticスキーマ定義。

要件トレーサビリティ:
  要件ID: RQ-DT-USER-ENTITY
  設計ID: DS-SC-USER-DT-USER-ENTITY
  要件概要: ユーザーの入出力データ仕様を定義する（パスワードハッシュはレスポンスに含めない）
  設計概要: UserCreate(username, login_id, password, role)、UserUpdate(username, login_id, password, role)、UserResponse(id, username, login_id, role)を定義する
  呼び出し先設計ID: DS-SC-USER-DT-USER-ENTITY
  呼び出し元設計ID: DS-IF-LIST-USERS-FT-DELETE-USER, DS-IF-CREATE-USER-FT-CREATE-USER
"""

from typing import Optional
from pydantic import BaseModel


class UserCreate(BaseModel):
    """
    ユーザー登録リクエストスキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-CREATE-USER
      設計ID: DS-SC-USER-DT-USER-ENTITY
      要件概要: ユーザー登録のリクエストデータ仕様
      設計概要: username, login_id, password, roleを必須フィールドとして定義する
      呼び出し先設計ID: DS-SC-USER-DT-USER-ENTITY
      呼び出し元設計ID: DS-IF-CREATE-USER-FT-CREATE-USER
    """

    username: str
    login_id: str
    password: str
    role: str


class UserUpdate(BaseModel):
    """
    ユーザー更新リクエストスキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-EDIT-USER
      設計ID: DS-SC-USER-DT-USER-ENTITY
      要件概要: ユーザー編集のリクエストデータ仕様
      設計概要: username, login_id, password, roleを任意フィールドとして定義する
      呼び出し先設計ID: DS-SC-USER-DT-USER-ENTITY
      呼び出し元設計ID: DS-IF-UPDATE-USER-FT-EDIT-USER
    """

    username: Optional[str] = None
    login_id: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None


class UserResponse(BaseModel):
    """
    ユーザーレスポンススキーマ（パスワードハッシュを除く）。

    要件トレーサビリティ:
      要件ID: RQ-FT-LIST-EQUIPMENT
      設計ID: DS-SC-USER-DT-USER-ENTITY
      要件概要: ユーザー情報の出力データ仕様（パスワードハッシュを含まない）
      設計概要: id, username, login_id, roleを返す。password_hashは含めない
      呼び出し先設計ID: DS-SC-USER-DT-USER-ENTITY
      呼び出し元設計ID: DS-IF-LIST-USERS-FT-DELETE-USER
    """

    id: int
    username: str
    login_id: str
    role: str

    model_config = {"from_attributes": True}
