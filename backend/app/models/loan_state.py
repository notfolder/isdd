"""
貸出状態ORMモデルモジュール。

要件トレーサビリティ:
  要件ID: RQ-DT-LOAN-STATE-ENTITY
  設計ID: DS-MD-LOAN-STATE-DT-LOAN-STATE-ENTITY
  要件概要: 貸出状態エンティティ（備品ID・利用者ログインID・貸出日）をDBに永続化する。
  設計概要: SQLAlchemy の DeclarativeBase を継承し、loan_state テーブルを定義する。equipment と user の外部キーを持つ。
  呼び出し先: なし
  呼び出し元: DS-CL-LOAN-STATE-REPO-DT-LOAN-STATE-ENTITY, DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
"""
from sqlalchemy import Column, String, ForeignKey
from app.core.database import Base


class LoanState(Base):
    """
    貸出状態ORMモデル。loan_state テーブルに対応する。

    Attributes:
        equipment_id (str): 備品ID（主キー・外部キー）。
        user_login_id (str): 貸出先利用者のログインID（外部キー）。
        loan_date (str): 貸出日（YYYY-MM-DD 文字列）。

    要件トレーサビリティ:
      要件ID: RQ-DT-LOAN-STATE-ENTITY
      設計ID: DS-MD-LOAN-STATE-DT-LOAN-STATE-ENTITY
      要件概要: 備品の貸出先利用者と貸出日を管理する。備品は同時に1名のみに貸出可能。
      設計概要: equipment_id を主キー兼外部キーとし、1備品1貸出の制約を表現する。
      呼び出し先: なし
      呼び出し元: DS-CL-LOAN-STATE-REPO-DT-LOAN-STATE-ENTITY
    """
    __tablename__ = "loan_state"

    equipment_id = Column(String, ForeignKey("equipment.equipment_id"), primary_key=True)
    user_login_id = Column(String, ForeignKey("user.login_id"), nullable=False)
    loan_date = Column(String, nullable=False)
