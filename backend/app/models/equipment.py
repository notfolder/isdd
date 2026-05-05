"""
備品ORMモデルモジュール。

要件トレーサビリティ:
  要件ID: RQ-DT-EQUIPMENT-ENTITY
  設計ID: DS-MD-EQUIPMENT-DT-EQUIPMENT-ENTITY
  要件概要: 備品エンティティ（備品ID・名称・貸出状態）をDBに永続化する。
  設計概要: SQLAlchemy の DeclarativeBase を継承し、equipment テーブルを定義する。
  呼び出し先: なし
  呼び出し元: DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY, DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
"""
from sqlalchemy import Column, String
from app.core.database import Base


class Equipment(Base):
    """
    備品ORMモデル。equipment テーブルに対応する。

    Attributes:
        equipment_id (str): 備品ID（主キー）。
        name (str): 備品名称。
        status (str): 貸出状態。'available' または 'loaned'。

    要件トレーサビリティ:
      要件ID: RQ-DT-EQUIPMENT-ENTITY
      設計ID: DS-MD-EQUIPMENT-DT-EQUIPMENT-ENTITY
      要件概要: 備品ID・名称・貸出状態（利用可能/貸出中）を保持する。
      設計概要: equipment_id を主キーとし、status のデフォルトを 'available' とする。
      呼び出し先: なし
      呼び出し元: DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY
    """
    __tablename__ = "equipment"

    equipment_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="available")
