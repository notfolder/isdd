"""
貸出記録エンティティのSQLAlchemyモデル。

要件トレーサビリティ:
  要件ID: RQ-DT-LOAN-ENTITY
  設計ID: DS-SC-LOAN-DT-LOAN-ENTITY
  要件概要: 貸出記録（id, equipment_id FK, user_id FK, lent_at, returned_at NULL）を永続化する
  設計概要: loansテーブルをSQLAlchemyのDeclarativeBaseで定義する。returned_atはNULL許容
  呼び出し先設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
  呼び出し元設計ID: DS-CL-LOAN-SERVICE-FT-LEND-EQUIPMENT
"""

from sqlalchemy import Column, Integer, String, Date, ForeignKey
from app.db.database import Base


class Loan(Base):
    """
    貸出記録テーブルモデル。

    要件トレーサビリティ:
      要件ID: RQ-DT-LOAN-ENTITY
      設計ID: DS-SC-LOAN-DT-LOAN-ENTITY
      要件概要: 誰がいつ備品を借りたかを記録する
      設計概要: id(PK), equipment_id(FK), user_id(FK), lent_at(DATE NOT NULL), returned_at(DATE NULL)のカラムを持つ
      呼び出し先設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
      呼び出し元設計ID: DS-CL-LOAN-SERVICE-FT-LEND-EQUIPMENT
    """

    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lent_at = Column(Date, nullable=False)
    returned_at = Column(Date, nullable=True)
