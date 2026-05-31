"""
データベース接続・セッション管理モジュール。

要件トレーサビリティ:
  要件ID: RQ-DT-DB-REQUIRED
  設計ID: DS-MD-SQLITE-DT-DB-REQUIRED
  要件概要: 備品・ユーザー・貸出記録のリレーショナルデータを保持するDBが必要。
  設計概要: SQLiteを使用したファイルベースDBをSQLAlchemyで管理する。
  呼び出し先設計ID: DS-SC-EQUIPMENT-DT-ENTITY-EQUIPMENT, DS-SC-USER-DT-ENTITY-USER, DS-SC-LENDING-DT-ENTITY-LENDING
  呼び出し元設計ID: DS-MD-BACKEND-FT-LIST-EQUIPMENT
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """
    SQLAlchemy宣言的基底クラス。全モデルクラスの基底となる。

    要件トレーサビリティ:
      要件ID: RQ-DT-DB-REQUIRED
      設計ID: DS-MD-SQLITE-DT-DB-REQUIRED
      要件概要: 備品・ユーザー・貸出記録のリレーショナルデータを保持するDBが必要。
      設計概要: SQLAlchemy 2.x の DeclarativeBase を継承した基底クラス。全モデルがこれを継承する。
      呼び出し先設計ID: DS-SC-EQUIPMENT-DT-ENTITY-EQUIPMENT, DS-SC-USER-DT-ENTITY-USER, DS-SC-LENDING-DT-ENTITY-LENDING
      呼び出し元設計ID: DS-MD-BACKEND-FT-LIST-EQUIPMENT
    """
    pass


def get_db():
    """
    DBセッションを生成してDI経由で提供する。

    Yields:
        Session: SQLAlchemyセッション。

    要件トレーサビリティ:
      要件ID: RQ-DT-DB-REQUIRED
      設計ID: DS-FN-LOGIN-FT-LOGIN
      要件概要: DBが必要。備品・ユーザー・貸出記録のリレーショナルデータを保持する。
      設計概要: FastAPIのDependsで使用するジェネレーター関数。リクエストごとにセッションを生成・クローズする。
      呼び出し先設計ID: DS-MD-SQLITE-DT-DB-REQUIRED
      呼び出し元設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN, DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT, DS-IF-LIST-USERS-FT-MANAGE-USERS
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    DBスキーマを初期化する（テーブル未存在時のみ作成）。

    要件トレーサビリティ:
      要件ID: RQ-DT-DB-REQUIRED
      設計ID: DS-MD-SQLITE-DT-DB-REQUIRED
      要件概要: DBが必要。起動時にテーブルを自動生成する。
      設計概要: Base.metadata.create_allでDDLを実行し、テーブルが存在しない場合のみ作成する。
      呼び出し先設計ID: DS-SC-EQUIPMENT-DT-ENTITY-EQUIPMENT, DS-SC-USER-DT-ENTITY-USER, DS-SC-LENDING-DT-ENTITY-LENDING
      呼び出し元設計ID: DS-MD-BACKEND-FT-LIST-EQUIPMENT
    """
    from app.models import equipment, user, lending  # noqa: F401
    Base.metadata.create_all(bind=engine)
