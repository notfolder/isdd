"""
Pydantic スキーマ - リクエスト/レスポンスモデル

要件トレーサビリティ:
  要件ID: RQ-DT-ITEM, RQ-DT-USER, RQ-FT-LOGIN
  設計ID: DS-CL-SCHEMAS-DT-ITEM
  要件概要: 備品と利用者のデータ構造を定義し、APIのリクエスト/レスポンスに使用する
  設計概要: Pydanticを使用して、ログイン、備品、利用者のスキーマを定義する
  呼び出し先: なし
  呼び出し元: DS-CL-AUTH-ROUTER-FT-LOGIN, DS-CL-ITEM-ROUTER-FT-REGISTER-ITEM, DS-CL-USER-ROUTER-FT-REGISTER-USER
"""

from pydantic import BaseModel, Field
from typing import Optional


# ログイン関連スキーマ
# 要件ID: RQ-FT-LOGIN
# 設計ID: DS-CL-SCHEMAS-DT-ITEM

class LoginRequest(BaseModel):
    """
    ログインリクエストスキーマ
    
    要件ID: RQ-FT-LOGIN
    設計ID: DS-CL-SCHEMAS-DT-ITEM
    要件概要: ユーザーIDとパスワードでログインする
    設計概要: ユーザーIDとパスワードを受け取る
    """
    user_id: str = Field(..., description="ユーザーID")
    password: str = Field(..., description="パスワード")


class LoginResponse(BaseModel):
    """
    ログインレスポンススキーマ
    
    要件ID: RQ-FT-LOGIN
    設計ID: DS-CL-SCHEMAS-DT-ITEM
    要件概要: ログイン成功時にJWTトークンとユーザー情報を返す
    設計概要: JWTトークン、ユーザーID、権限を返す
    """
    access_token: str = Field(..., description="JWTアクセストークン")
    token_type: str = Field(default="bearer", description="トークンタイプ")
    user_id: str = Field(..., description="ユーザーID")
    role: str = Field(..., description="権限（管理者/一般利用者）")


# 備品関連スキーマ
# 要件ID: RQ-DT-ITEM, RQ-FT-REGISTER-ITEM
# 設計ID: DS-CL-SCHEMAS-DT-ITEM

class ItemBase(BaseModel):
    """
    備品ベーススキーマ
    
    要件ID: RQ-DT-ITEM
    設計ID: DS-CL-SCHEMAS-DT-ITEM
    要件概要: 備品の基本情報（資産管理番号、名称）
    設計概要: 備品の共通フィールドを定義
    """
    asset_number: str = Field(..., description="資産管理番号")
    name: str = Field(..., description="備品名称")


class ItemResponse(ItemBase):
    """
    備品レスポンススキーマ
    
    要件ID: RQ-DT-ITEM, RQ-FT-VIEW-ITEM-LIST
    設計ID: DS-CL-SCHEMAS-DT-ITEM
    要件概要: 備品情報と貸出状況を返す
    設計概要: 備品の資産管理番号、名称、借り主、ステータスを返す
    """
    borrower: Optional[str] = Field(None, description="借り主（貸出中の場合）")
    status: str = Field(..., description="ステータス（利用可能/貸出中）")


class ItemCreate(ItemBase):
    """
    備品登録リクエストスキーマ
    
    要件ID: RQ-FT-REGISTER-ITEM
    設計ID: DS-CL-SCHEMAS-DT-ITEM
    要件概要: 備品登録に必要な情報を受け取る
    設計概要: 資産管理番号と名称を受け取る
    """
    pass


class ItemUpdate(BaseModel):
    """
    備品更新リクエストスキーマ
    
    要件ID: RQ-FT-EDIT-ITEM
    設計ID: DS-CL-SCHEMAS-DT-ITEM
    要件概要: 備品情報の更新に必要な情報を受け取る
    設計概要: 名称のみを受け取る（資産管理番号は変更不可）
    """
    name: str = Field(..., description="備品名称")


class LendRequest(BaseModel):
    """
    貸出リクエストスキーマ
    
    要件ID: RQ-FT-LEND-ITEM
    設計ID: DS-CL-SCHEMAS-DT-ITEM
    要件概要: 備品の貸出に必要な情報を受け取る
    設計概要: 借り主（利用者の氏名）を受け取る
    """
    borrower: str = Field(..., description="借り主（利用者の氏名）")


# 利用者関連スキーマ
# 要件ID: RQ-DT-USER, RQ-FT-REGISTER-USER
# 設計ID: DS-CL-SCHEMAS-DT-ITEM

class UserBase(BaseModel):
    """
    利用者ベーススキーマ
    
    要件ID: RQ-DT-USER
    設計ID: DS-CL-SCHEMAS-DT-ITEM
    要件概要: 利用者の基本情報（ユーザーID、氏名、権限）
    設計概要: 利用者の共通フィールドを定義
    """
    user_id: str = Field(..., description="ユーザーID")
    name: str = Field(..., description="氏名")
    role: str = Field(..., description="権限（管理者/一般利用者）")


class UserResponse(UserBase):
    """
    利用者レスポンススキーマ
    
    要件ID: RQ-DT-USER, RQ-FT-VIEW-USER-LIST
    設計ID: DS-CL-SCHEMAS-DT-ITEM
    要件概要: 利用者情報を返す
    設計概要: ユーザーID、氏名、権限を返す（パスワードは含めない）
    """
    pass


class UserCreate(UserBase):
    """
    利用者登録リクエストスキーマ
    
    要件ID: RQ-FT-REGISTER-USER
    設計ID: DS-CL-SCHEMAS-DT-ITEM
    要件概要: 利用者登録に必要な情報を受け取る
    設計概要: ユーザーID、氏名、パスワード、権限を受け取る
    """
    password: str = Field(..., description="パスワード")


class UserUpdate(BaseModel):
    """
    利用者更新リクエストスキーマ
    
    要件ID: RQ-FT-EDIT-USER
    設計ID: DS-CL-SCHEMAS-DT-ITEM
    要件概要: 利用者情報の更新に必要な情報を受け取る
    設計概要: 氏名、パスワード（オプション）、権限を受け取る（ユーザーIDは変更不可）
    """
    name: str = Field(..., description="氏名")
    password: Optional[str] = Field(None, description="パスワード（変更する場合のみ）")
    role: str = Field(..., description="権限（管理者/一般利用者）")
