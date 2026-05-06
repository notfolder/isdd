"""
貸出スキーマモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-LOAN-EQUIPMENT, RQ-DT-LOAN-STATE-ENTITY
  設計ID: DS-SC-LOAN-STATE-DT-LOAN-STATE-ENTITY
  要件概要: 備品貸出操作のAPIリクエストデータ構造を定義する。
  設計概要: Pydantic BaseModel で貸出リクエストスキーマを定義する。
  呼び出し先: なし
  呼び出し元: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT, DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
"""
from pydantic import BaseModel


class LoanCreate(BaseModel):
    """
    貸出登録リクエストスキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOAN-EQUIPMENT, RQ-DT-LOAN-STATE-ENTITY
      設計ID: DS-SC-LOAN-STATE-DT-LOAN-STATE-ENTITY
      要件概要: 管理者が貸出先利用者と貸出日を指定して備品を貸出できる。
      設計概要: user_login_id と loan_date を受け取る貸出リクエストスキーマ。
      呼び出し先: なし
      呼び出し元: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT
    """

    user_login_id: str
    loan_date: str
