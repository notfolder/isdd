"""
備品エンティティのSQLAlchemyモデル。

要件トレーサビリティ:
  要件ID: RQ-DT-EQUIPMENT-ENTITY
  設計ID: DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
  要件概要: 備品（id, asset_number UNIQUE, name, status）を永続化する
  設計概要: equipmentテーブルをSQLAlchemyのDeclarativeBaseで定義する。statusはavailable/lentのCHECK制約付き
  呼び出し先設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
  呼び出し元設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT, DS-CL-LOAN-SERVICE-FT-LEND-EQUIPMENT
"""

from sqlalchemy import Column, Integer, String, CheckConstraint
from app.db.database import Base


class Equipment(Base):
    """
    備品テーブルモデル。

    要件トレーサビリティ:
      要件ID: RQ-DT-EQUIPMENT-ENTITY
      設計ID: DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
      要件概要: 備品の資産管理番号・名称・状態を管理する
      設計概要: id(PK), asset_number(UNIQUE), name(NOT NULL), status(available/lent)のカラムを持つ
      呼び出し先設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
      呼び出し元設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
    """

    __tablename__ = "equipment"
    __table_args__ = (
        CheckConstraint("status IN ('available', 'lent')", name="check_equipment_status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_number = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="available")
