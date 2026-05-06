"""
利用者スキーマモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-MANAGE-BORROWER, RQ-DT-BORROWER-ENTITY
  設計ID: DS-SC-USER-DT-BORROWER-ENTITY
  要件概要: 利用者管理・貸出操作のAPIリクエスト/レスポンスデータ構造を定義する。
  設計概要: Pydantic BaseModel で利用者の入出力スキーマを型安全に定義する。
  呼び出し先: なし
  呼び出し元: DS-CL-USER-ROUTER-FT-MANAGE-BORROWER, DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
"""
from typing import Optional
from pydantic import BaseModel


class UserCreate(BaseModel):
    """
    利用者登録リクエストスキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-BORROWER, RQ-DT-BORROWER-ENTITY
      設計ID: DS-SC-USER-DT-BORROWER-ENTITY
      要件概要: 管理者がlogin_id・表示名・パスワード・ロールを指定して利用者を登録できる。
      設計概要: login_id・display_name・password・role を受け取る登録リクエストスキーマ。
      呼び出し先: なし
      呼び出し元: DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
    """

    login_id: str
    display_name: str
    password: str
    role: str


class UserUpdate(BaseModel):
    """
    利用者更新リクエストスキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-BORROWER, RQ-DT-BORROWER-ENTITY
      設計ID: DS-SC-USER-DT-BORROWER-ENTITY
      要件概要: 管理者が利用者の表示名・パスワード・ロールを更新できる。
      設計概要: 更新対象フィールド（display_name・password・role）を受け取るスキーマ。全フィールド任意。
      呼び出し先: なし
      呼び出し元: DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
    """

    display_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None


class UserResponse(BaseModel):
    """
    利用者レスポンススキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-BORROWER, RQ-DT-BORROWER-ENTITY
      設計ID: DS-SC-USER-DT-BORROWER-ENTITY
      要件概要: 利用者のlogin_id・表示名・ロールを含むレスポンスを返す。
      設計概要: User モデルから login_id・display_name・role を返すレスポンススキーマ。
      呼び出し先: なし
      呼び出し元: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER, DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
    """

    login_id: str
    display_name: str
    role: str

    class Config:
        from_attributes = True


class UserForLoan(BaseModel):
    """
    貸出画面用利用者スキーマ。貸出先候補一覧で使用する簡易形式。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOAN-EQUIPMENT, RQ-DT-BORROWER-ENTITY
      設計ID: DS-SC-USER-DT-BORROWER-ENTITY
      要件概要: 貸出操作時に管理者が利用者一覧から貸出先を選択できる。
      設計概要: 貸出先選択用に login_id と display_name のみを返す簡易スキーマ。
      呼び出し先: なし
      呼び出し元: DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
    """

    login_id: str
    display_name: str

    class Config:
        from_attributes = True
