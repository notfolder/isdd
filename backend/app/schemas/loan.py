"""
貸出記録のPydanticスキーマ定義。

要件トレーサビリティ:
  要件ID: RQ-DT-LOAN-ENTITY
  設計ID: DS-SC-LOAN-DT-LOAN-ENTITY
  要件概要: 貸出記録の入出力データ仕様を定義する
  設計概要: LoanCreate(equipment_id, user_id)、LoanResponse(id, equipment_id, user_id, lent_at, returned_at)を定義する
  呼び出し先設計ID: DS-SC-LOAN-DT-LOAN-ENTITY
  呼び出し元設計ID: DS-IF-LEND-EQUIPMENT-FT-LEND-EQUIPMENT, DS-IF-RETURN-EQUIPMENT-FT-RETURN-EQUIPMENT
"""

from typing import Optional
from datetime import date
from pydantic import BaseModel


class LoanCreate(BaseModel):
    """
    貸出登録リクエストスキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-LEND-EQUIPMENT
      設計ID: DS-SC-LOAN-DT-LOAN-ENTITY
      要件概要: 貸出登録のリクエストデータ仕様
      設計概要: equipment_idとuser_idを必須フィールドとして定義する
      呼び出し先設計ID: DS-SC-LOAN-DT-LOAN-ENTITY
      呼び出し元設計ID: DS-IF-LEND-EQUIPMENT-FT-LEND-EQUIPMENT
    """

    equipment_id: int
    user_id: int


class LoanResponse(BaseModel):
    """
    貸出記録レスポンススキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-LEND-EQUIPMENT
      設計ID: DS-SC-LOAN-DT-LOAN-ENTITY
      要件概要: 貸出記録の出力データ仕様
      設計概要: id, equipment_id, user_id, lent_at, returned_atを返す
      呼び出し先設計ID: DS-SC-LOAN-DT-LOAN-ENTITY
      呼び出し元設計ID: DS-IF-LEND-EQUIPMENT-FT-LEND-EQUIPMENT
    """

    id: int
    equipment_id: int
    user_id: int
    lent_at: date
    returned_at: Optional[date] = None

    model_config = {"from_attributes": True}
