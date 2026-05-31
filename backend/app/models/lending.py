"""
貸出記録テーブルモデル定義モジュール。

要件トレーサビリティ:
  要件ID: RQ-DT-ENTITY-LENDING
  設計ID: DS-SC-LENDING-DT-ENTITY-LENDING
  要件概要: 貸出記録エンティティ。現在の貸出情報のみ保持（履歴なし）。返却時に削除する。
  設計概要: equipment_numberにUNIQUE制約を付け1備品1貸出を保証する。返却時にレコードを削除する。
  呼び出し先設計ID: DS-SC-EQUIPMENT-DT-ENTITY-EQUIPMENT, DS-SC-USER-DT-ENTITY-USER
  呼び出し元設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT, DS-MD-SQLITE-DT-DB-REQUIRED
"""

import datetime
from sqlalchemy import String, Integer, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class LendingRecord(Base):
    """
    貸出記録テーブルのSQLAlchemyモデル。

    要件トレーサビリティ:
      要件ID: RQ-DT-ENTITY-LENDING
      設計ID: DS-SC-LENDING-DT-ENTITY-LENDING
      要件概要: 貸出記録。1備品につき最大1件。返却時に物理削除し履歴は保持しない。
      設計概要: equipment_numberにUNIQUE制約で1備品1貸出を保証。外部キーでequipment・usersと連結する。
      呼び出し先設計ID: DS-SC-EQUIPMENT-DT-ENTITY-EQUIPMENT, DS-SC-USER-DT-ENTITY-USER
      呼び出し元設計ID: DS-FN-RECORD-LENDING-FT-RECORD-LENDING, DS-FN-RECORD-RETURN-FT-RECORD-RETURN
    """

    __tablename__ = "lending_records"
    __table_args__ = (
        UniqueConstraint("equipment_number", name="uq_lending_equipment"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    equipment_number: Mapped[str] = mapped_column(
        String(50), ForeignKey("equipment.management_number"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    lend_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    expected_return_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)

    equipment: Mapped["Equipment"] = relationship(  # type: ignore[name-defined]
        "Equipment", back_populates="lending_record"
    )
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="lending_records"
    )
