"""
備品のPydanticスキーマ定義。

要件トレーサビリティ:
  要件ID: RQ-DT-EQUIPMENT-ENTITY
  設計ID: DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
  要件概要: 備品の入出力データ仕様を定義する
  設計概要: EquipmentCreate(asset_number, name)、EquipmentUpdate(name)、EquipmentResponse(id, asset_number, name, status, borrower_name, lent_at)を定義する
  呼び出し先設計ID: DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
  呼び出し元設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT, DS-IF-CREATE-EQUIPMENT-FT-CREATE-EQUIPMENT
"""

from typing import Optional
from datetime import date
from pydantic import BaseModel


class EquipmentCreate(BaseModel):
    """
    備品登録リクエストスキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-CREATE-EQUIPMENT
      設計ID: DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
      要件概要: 備品登録のリクエストデータ仕様
      設計概要: asset_numberとnameを必須フィールドとして定義する
      呼び出し先設計ID: DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
      呼び出し元設計ID: DS-IF-CREATE-EQUIPMENT-FT-CREATE-EQUIPMENT
    """

    asset_number: str
    name: str


class EquipmentUpdate(BaseModel):
    """
    備品更新リクエストスキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-EDIT-EQUIPMENT
      設計ID: DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
      要件概要: 備品編集のリクエストデータ仕様
      設計概要: asset_numberとnameを更新可能フィールドとして定義する
      呼び出し先設計ID: DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
      呼び出し元設計ID: DS-IF-UPDATE-EQUIPMENT-FT-EDIT-EQUIPMENT
    """

    asset_number: Optional[str] = None
    name: Optional[str] = None


class EquipmentResponse(BaseModel):
    """
    備品レスポンススキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-LIST-EQUIPMENT
      設計ID: DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
      要件概要: 備品一覧の出力データ仕様（貸出中の場合は貸出先ユーザー名・貸出日を含む）
      設計概要: id, asset_number, name, status, borrower_name(Optional), lent_at(Optional)を返す
      呼び出し先設計ID: DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
      呼び出し元設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
    """

    id: int
    asset_number: str
    name: str
    status: str
    borrower_name: Optional[str] = None
    lent_at: Optional[date] = None
    loan_id: Optional[int] = None

    model_config = {"from_attributes": True}
