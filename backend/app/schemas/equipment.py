"""
備品スキーマ定義モジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-LIST-EQUIPMENT
  設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
  要件概要: 全備品の状態・貸出情報を一覧で取得する。管理番号・備品名・状態・貸出先氏名・返却予定日を返す。
  設計概要: 備品CRUDおよび貸出処理のリクエスト・レスポンスPydanticスキーマを定義する。
  呼び出し先設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
  呼び出し元設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
"""

import datetime
from typing import Optional
from pydantic import BaseModel


class EquipmentCreate(BaseModel):
    """
    備品登録リクエストスキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-CREATE-EQUIPMENT
      設計ID: DS-IF-CREATE-EQUIPMENT-FT-CREATE-EQUIPMENT
      要件概要: 管理番号と備品名を受け取り備品を登録する。
      設計概要: management_number・nameの2フィールドを持つ登録リクエストスキーマ。
      呼び出し先設計ID: DS-FN-CREATE-EQUIPMENT-FT-CREATE-EQUIPMENT
      呼び出し元設計ID: DS-IF-CREATE-EQUIPMENT-FT-CREATE-EQUIPMENT
    """

    management_number: str
    name: str


class EquipmentUpdate(BaseModel):
    """
    備品更新リクエストスキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-UPDATE-EQUIPMENT
      設計ID: DS-IF-UPDATE-EQUIPMENT-FT-UPDATE-EQUIPMENT
      要件概要: 備品の管理番号・備品名を更新する。
      設計概要: nameフィールドを持つ更新リクエストスキーマ。管理番号はパスパラメータで指定する。
      呼び出し先設計ID: DS-FN-UPDATE-EQUIPMENT-FT-UPDATE-EQUIPMENT
      呼び出し元設計ID: DS-IF-UPDATE-EQUIPMENT-FT-UPDATE-EQUIPMENT
    """

    name: str


class LendingInfo(BaseModel):
    """
    貸出情報サブスキーマ（備品レスポンスに埋め込む）。

    要件トレーサビリティ:
      要件ID: RQ-FT-LIST-EQUIPMENT
      設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
      要件概要: 貸出中備品の貸出先氏名・貸出日・返却予定日を一覧で表示する。
      設計概要: 備品レスポンスに埋め込む貸出情報サブスキーマ。貸出先氏名・日付を持つ。
      呼び出し先設計ID: なし
      呼び出し元設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
    """

    user_id: int
    user_name: str
    lend_date: datetime.date
    expected_return_date: datetime.date


class EquipmentResponse(BaseModel):
    """
    備品レスポンススキーマ（状態・貸出情報含む）。

    要件トレーサビリティ:
      要件ID: RQ-FT-LIST-EQUIPMENT
      設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
      要件概要: 全備品の管理番号・備品名・状態（在庫中/貸出中）・貸出情報を返す。
      設計概要: management_number・name・status・lending_infoを持つレスポンス。statusはlending_recordの有無で決定。
      呼び出し先設計ID: なし
      呼び出し元設計ID: DS-FN-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
    """

    management_number: str
    name: str
    status: str
    lending_info: Optional[LendingInfo] = None

    model_config = {"from_attributes": True}


class LendingCreate(BaseModel):
    """
    貸出処理リクエストスキーマ。

    要件トレーサビリティ:
      要件ID: RQ-FT-RECORD-LENDING
      設計ID: DS-IF-RECORD-LENDING-FT-RECORD-LENDING
      要件概要: 貸出先ユーザーID・貸出日・返却予定日を受け取り貸出処理を行う。
      設計概要: user_id・lend_date・expected_return_dateを持つ貸出処理リクエストスキーマ。
      呼び出し先設計ID: DS-FN-RECORD-LENDING-FT-RECORD-LENDING
      呼び出し元設計ID: DS-IF-RECORD-LENDING-FT-RECORD-LENDING
    """

    user_id: int
    lend_date: datetime.date
    expected_return_date: datetime.date
