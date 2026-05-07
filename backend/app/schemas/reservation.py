"""
予約スキーマモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-MAKE-RESERVATION, RQ-FT-CANCEL-RESERVATION, RQ-FT-VIEW-RESERVATION-CALENDAR
  設計ID: DS-EV-RESERVATION-CREATE-FT-MAKE-RESERVATION, DS-EV-RESERVATION-RESPONSE-FT-VIEW-RESERVATION-CALENDAR
  要件概要: 予約登録・レスポンスのAPIリクエスト/レスポンスデータ構造を定義する。
  設計概要: Pydantic BaseModel で入出力スキーマを型安全に定義する。
  呼び出し先: なし
  呼び出し元: DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION, DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION
"""
from typing import Optional
from pydantic import BaseModel


class ReservationCreate(BaseModel):
    """
    予約登録リクエストスキーマ。

    Attributes:
        start_date (str): 予約開始日（YYYY-MM-DD形式、必須）。
        end_date (str): 予約終了日（YYYY-MM-DD形式、必須、start_date 以降）。
        user_login_id (Optional[str]): 予約者ログインID（管理者のみ指定可。一般利用者は自動的に自分のID）。

    要件トレーサビリティ:
      要件ID: RQ-FT-MAKE-RESERVATION
      設計ID: DS-EV-RESERVATION-CREATE-FT-MAKE-RESERVATION
      要件概要: 開始日・終了日・予約者（管理者のみ指定可）を受け取る予約登録リクエスト。
      設計概要: start_date・end_date は必須。user_login_id は管理者のみ有効。
      呼び出し先: なし
      呼び出し元: DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION
    """

    start_date: str
    end_date: str
    user_login_id: Optional[str] = None


class ReservationResponse(BaseModel):
    """
    予約レスポンススキーマ。

    Attributes:
        reservation_id (str): 予約ID（UUID形式）。
        equipment_id (str): 予約対象の備品ID。
        user_login_id (str): 予約者のログインID。
        user_display_name (str): 予約者の表示名（JOIN で取得）。
        start_date (str): 予約開始日。
        end_date (str): 予約終了日。

    要件トレーサビリティ:
      要件ID: RQ-FT-VIEW-RESERVATION-CALENDAR
      設計ID: DS-EV-RESERVATION-RESPONSE-FT-VIEW-RESERVATION-CALENDAR
      要件概要: カレンダー画面の予約一覧に必要な全フィールドを返す。
      設計概要: reservation テーブルと user テーブルを JOIN して user_display_name を付与する。
      呼び出し先: なし
      呼び出し元: DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION, DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION
    """

    reservation_id: str
    equipment_id: str
    user_login_id: str
    user_display_name: str
    start_date: str
    end_date: str

    class Config:
        from_attributes = True
