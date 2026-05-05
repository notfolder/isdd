"""
利用者ORMモデルモジュール。

要件トレーサビリティ:
  要件ID: RQ-DT-USER-ENTITY
  設計ID: DS-MD-USER-DT-BORROWER-ENTITY
  要件概要: 利用者エンティティ（ログインID・表示名・パスワードハッシュ・ロール）をDBに永続化する。
  設計概要: SQLAlchemy の DeclarativeBase を継承し、user テーブルを定義する。
  呼び出し先: なし
  呼び出し元: DS-CL-USER-REPO-DT-BORROWER-ENTITY, DS-CL-AUTH-SERVICE-FT-LOGIN
"""
from sqlalchemy import Column, String
from app.core.database import Base


class User(Base):
    """
    利用者ORMモデル。user テーブルに対応する。

    Attributes:
        login_id (str): ログインID（主キー）。
        display_name (str): 表示名。
        password_hash (str): bcrypt ハッシュ済みパスワード。
        role (str): ロール。'admin' または 'general'。

    要件トレーサビリティ:
      要件ID: RQ-DT-USER-ENTITY, RQ-NF-PASSWORD-HASH
      設計ID: DS-MD-USER-DT-BORROWER-ENTITY
      要件概要: 管理者と一般利用者を区別するロールを持ち、パスワードはハッシュ化して保存する。
      設計概要: login_id を主キーとし、role カラムで権限を管理する。
      呼び出し先: なし
      呼び出し元: DS-CL-USER-REPO-DT-BORROWER-ENTITY
    """
    __tablename__ = "user"

    login_id = Column(String, primary_key=True, index=True)
    display_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
