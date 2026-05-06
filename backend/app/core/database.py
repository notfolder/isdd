"""
SQLAlchemy エンジン・セッション生成モジュール。

要件トレーサビリティ:
  要件ID: RQ-DT-APP-DATABASE-REQUIRED, RQ-DT-EQUIPMENT-ENTITY, RQ-DT-BORROWER-ENTITY
  設計ID: DS-MD-DATABASE-DT-EQUIPMENT-ENTITY
  要件概要: 備品・利用者・貸出状態を永続化するDBとしてSQLiteを使用する。
  設計概要: SQLAlchemy で SQLite に接続し、セッションファクトリと Base クラスを提供する。
  呼び出し先: なし
  呼び出し元: DS-MD-BACKEND-FT-MANAGE-EQUIPMENT, DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY, DS-CL-USER-REPO-DT-BORROWER-ENTITY, DS-CL-LOAN-STATE-REPO-DT-LOAN-STATE-ENTITY
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

SQLALCHEMY_DATABASE_URL = "sqlite:////app/data/app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """
    全ORMモデルの基底クラス。

    要件トレーサビリティ:
      要件ID: RQ-DT-APP-DATABASE-REQUIRED, RQ-DT-EQUIPMENT-ENTITY, RQ-DT-BORROWER-ENTITY
      設計ID: DS-MD-DATABASE-DT-EQUIPMENT-ENTITY
      要件概要: 備品・利用者・貸出状態を永続化するDBモデルの共通基底を提供する。
      設計概要: SQLAlchemy DeclarativeBase を継承した全モデル共通の基底クラス。
      呼び出し先: なし
      呼び出し元: DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY, DS-CL-USER-REPO-DT-BORROWER-ENTITY, DS-CL-LOAN-STATE-REPO-DT-LOAN-STATE-ENTITY
    """

    pass


def get_db():
    """
    FastAPI Depends 用 DB セッションジェネレーター。

    Yields:
        Session: SQLAlchemy セッション。リクエスト終了時に自動クローズ。

    要件トレーサビリティ:
      要件ID: RQ-DT-APP-DATABASE-REQUIRED
      設計ID: DS-MD-DATABASE-DT-EQUIPMENT-ENTITY
      要件概要: 全APIリクエストでDBセッションを安全に提供する。
      設計概要: セッションをyieldし、finally で必ず close する。
      呼び出し先: なし
      呼び出し元: DS-CL-AUTH-ROUTER-FT-LOGIN, DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT, DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
