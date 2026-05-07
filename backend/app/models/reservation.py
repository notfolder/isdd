"""
予約ORMモデルモジュール。

要件トレーサビリティ:
  要件ID: RQ-DT-RESERVATION-ENTITY, RQ-FT-MAKE-RESERVATION
  設計ID: DS-SC-RESERVATION-DT-RESERVATION-ENTITY
  要件概要: 予約エンティティ（予約ID・備品ID・利用者ログインID・開始日・終了日）をDBに永続化する。
  設計概要: SQLAlchemy の DeclarativeBase を継承し、reservation テーブルを定義する。
             equipment_id FK には ON DELETE CASCADE を設定する。
  呼び出し先: なし
  呼び出し元: DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY
"""
from sqlalchemy import Column, String, ForeignKey
from app.core.database import Base


class Reservation(Base):
    """
    予約ORMモデル。reservation テーブルに対応する。

    Attributes:
        reservation_id (str): 予約ID（主キー、UUID形式）。
        equipment_id (str): 予約対象の備品ID（FK→equipment.equipment_id ON DELETE CASCADE）。
        user_login_id (str): 予約者のログインID（FK→user.login_id）。
        start_date (str): 予約開始日（ISO 8601形式、例: 2026-06-01）。
        end_date (str): 予約終了日（ISO 8601形式、例: 2026-06-05）。start_date 以降であること。

    要件トレーサビリティ:
      要件ID: RQ-DT-RESERVATION-ENTITY
      設計ID: DS-SC-RESERVATION-DT-RESERVATION-ENTITY
      要件概要: 予約ID・備品ID・利用者ログインID・開始日・終了日を保持する。
      設計概要: reservation_id を主キーとし、equipment_id FK に ON DELETE CASCADE を設定する。
      呼び出し先: なし
      呼び出し元: DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY
    """
    __tablename__ = "reservation"

    reservation_id = Column(String, primary_key=True, index=True)
    equipment_id = Column(
        String,
        ForeignKey("equipment.equipment_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_login_id = Column(
        String,
        ForeignKey("user.login_id"),
        nullable=False,
    )
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
