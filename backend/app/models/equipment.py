"""
備品テーブルモデル定義モジュール。

要件トレーサビリティ:
  要件ID: RQ-DT-ENTITY-EQUIPMENT
  設計ID: DS-SC-EQUIPMENT-DT-ENTITY-EQUIPMENT
  要件概要: 備品エンティティ。管理番号・備品名を持ち、貸出記録と1対0〜1のリレーション。
  設計概要: SQLAlchemyモデルでequipmentテーブルを定義。management_numberを主キーとする。
  呼び出し先設計ID: DS-SC-LENDING-DT-ENTITY-LENDING
  呼び出し元設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT, DS-MD-SQLITE-DT-DB-REQUIRED
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Equipment(Base):
    """
    備品テーブルのSQLAlchemyモデル。

    要件トレーサビリティ:
      要件ID: RQ-DT-ENTITY-EQUIPMENT
      設計ID: DS-SC-EQUIPMENT-DT-ENTITY-EQUIPMENT
      要件概要: 備品エンティティ。管理番号・備品名を持つ。状態は貸出記録の存在で判定する。
      設計概要: management_numberを主キーとし、lending_recordsとone-to-oneのリレーションを持つ。
      呼び出し先設計ID: DS-SC-LENDING-DT-ENTITY-LENDING
      呼び出し元設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
    """

    __tablename__ = "equipment"

    management_number: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    lending_record: Mapped["LendingRecord"] = relationship(  # type: ignore[name-defined]
        "LendingRecord",
        back_populates="equipment",
        uselist=False,
        cascade="all, delete-orphan",
    )
