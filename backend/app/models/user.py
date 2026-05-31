"""
ユーザーテーブルモデル定義モジュール（社員マスター兼用）。

要件トレーサビリティ:
  要件ID: RQ-DT-ENTITY-USER
  設計ID: DS-SC-USER-DT-ENTITY-USER
  要件概要: ユーザーエンティティ。ログイン認証と社員マスターを一本化する。氏名・メール・パスワード・権限を持つ。
  設計概要: SQLAlchemyモデルでusersテーブルを定義。emailをUNIQUE制約付きで管理する。
  呼び出し先設計ID: DS-SC-LENDING-DT-ENTITY-LENDING
  呼び出し元設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USERS, DS-CL-AUTH-SERVICE-FT-LOGIN
"""

from sqlalchemy import String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    """
    ユーザーテーブルのSQLAlchemyモデル。

    要件トレーサビリティ:
      要件ID: RQ-DT-ENTITY-USER
      設計ID: DS-SC-USER-DT-ENTITY-USER
      要件概要: ユーザーエンティティ。ログインと社員マスターを一本化。権限は管理者/一般の2種。
      設計概要: idを自動採番主キーとし、emailにUNIQUE制約。roleはCHECK制約でadmin/generalのみ許容。
      呼び出し先設計ID: DS-SC-LENDING-DT-ENTITY-LENDING
      呼び出し元設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USERS, DS-CL-AUTH-SERVICE-FT-LOGIN
    """

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'general')", name="ck_users_role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(10), nullable=False, default="general")

    lending_records: Mapped[list["LendingRecord"]] = relationship(  # type: ignore[name-defined]
        "LendingRecord",
        back_populates="user",
    )
