"""
備品スキーマモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-MANAGE-EQUIPMENT, RQ-DT-EQUIPMENT-ENTITY, RQ-DT-LOAN-STATE-ENTITY
  設計ID: DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
  要件概要: 備品CRUD・貸出・返却のAPIリクエスト/レスポンスデータ構造を定義する。
  設計概要: Pydantic BaseModel で入出力スキーマを型安全に定義する。
  呼び出し先: なし
  呼び出し元: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT, DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
"""
from typing import Optional
from pydantic import BaseModel


class EquipmentCreate(BaseModel):
    """
    備品登録リクエストスキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-EQUIPMENT, RQ-DT-EQUIPMENT-ENTITY
      設計ID: DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
      要件概要: 管理者が備品IDと名称を指定して新規備品を登録できる。
      設計概要: equipment_id（管理者入力・一意）と name を受け取るリクエストスキーマ。
      呼び出し先: なし
      呼び出し元: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT
    """

    equipment_id: str
    name: str


class EquipmentUpdate(BaseModel):
    """
    備品更新リクエストスキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-EQUIPMENT, RQ-DT-EQUIPMENT-ENTITY
      設計ID: DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
      要件概要: 管理者が備品名称を更新できる。
      設計概要: 更新対象フィールド（name のみ）を受け取るリクエストスキーマ。
      呼び出し先: なし
      呼び出し元: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT
    """

    name: str


class LoanInfo(BaseModel):
    """
    貸出情報スキーマ。備品レスポンスに埋め込まれる貸出状態情報。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOAN-EQUIPMENT, RQ-DT-LOAN-STATE-ENTITY
      設計ID: DS-SC-LOAN-STATE-DT-LOAN-STATE-ENTITY
      要件概要: 備品一覧に貸出先利用者名と貸出日を表示する。
      設計概要: LoanState + User を結合して構築する貸出情報の組み込みスキーマ。
      呼び出し先: なし
      呼び出し元: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
    """

    user_login_id: str
    user_display_name: str
    loan_date: str


class EquipmentResponse(BaseModel):
    """
    備品レスポンススキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-EQUIPMENT, RQ-FT-LOAN-EQUIPMENT, RQ-DT-EQUIPMENT-ENTITY
      設計ID: DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
      要件概要: 備品ID・名称・貸出状態・貸出情報を含むレスポンスを返す。
      設計概要: Equipment モデルと LoanInfo を組み合わせたレスポンススキーマ。
      呼び出し先: なし
      呼び出し元: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT, DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT
    """

    equipment_id: str
    name: str
    status: str
    loan_info: Optional[LoanInfo] = None

    class Config:
        from_attributes = True
