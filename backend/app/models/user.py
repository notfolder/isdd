"""
ユーザーエンティティのSQLAlchemyモデル。

要件トレーサビリティ:
  要件ID: RQ-DT-USER-ENTITY
  設計ID: DS-SC-USER-DT-USER-ENTITY
  要件概要: ユーザー（id, username, login_id UNIQUE, password_hash, role）を永続化する
  設計概要: usersテーブルをSQLAlchemyのDeclarativeBaseで定義する。roleはadmin/generalのCHECK制約付き
  呼び出し先設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
  呼び出し元設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN, DS-CL-USER-SERVICE-FT-CREATE-USER
"""

from sqlalchemy import Column, Integer, String, CheckConstraint
from app.db.database import Base


class User(Base):
    """
    ユーザーテーブルモデル。

    要件トレーサビリティ:
      要件ID: RQ-DT-USER-ENTITY
      設計ID: DS-SC-USER-DT-USER-ENTITY
      要件概要: ユーザーのログインIDと役割を管理し認証・認可に使用する
      設計概要: id(PK), username(NOT NULL), login_id(UNIQUE NOT NULL), password_hash(NOT NULL), role(admin/general)のカラムを持つ
      呼び出し先設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
      呼び出し元設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
    """

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'general')", name="check_user_role"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)
    login_id = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
