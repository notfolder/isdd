"""
SQLAlchemyセッション管理とDB設定。

要件トレーサビリティ:
  要件ID: RQ-NF-CONCURRENT-USERS, RQ-DT-INTERNAL-DATA
  設計ID: DS-FN-CONFIGURE-DB-NF-CONCURRENT-USERS, DS-SC-INTERNAL-DATA-DT-INTERNAL-DATA
  要件概要: SQLite WALモードで最大10名の同時接続を保証し、全データをアプリ内蔵DBで管理する
  設計概要: SQLAlchemyのcreate_engineでSQLiteに接続し、起動時にPRAGMA journal_mode=WALを実行する
  呼び出し先設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
  呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:////data/app.db"

# SQLiteのcheck_same_thread=Falseは複数スレッドからのアクセスを許可するために必要
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


def set_wal_mode(dbapi_connection, connection_record):
    """
    SQLite WALモードを有効化する。

    要件トレーサビリティ:
      要件ID: RQ-NF-CONCURRENT-USERS
      設計ID: DS-FN-CONFIGURE-DB-NF-CONCURRENT-USERS
      要件概要: 最大10名の同時接続を保証する
      設計概要: SQLite WALモードを起動時に有効化し、同時接続時の読み取りブロックを防ぐ
      呼び出し先設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
      呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


event.listen(engine, "connect", set_wal_mode)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    DBセッションの依存注入用ジェネレーター。

    要件トレーサビリティ:
      要件ID: RQ-DT-DB-REQUIRED
      設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
      要件概要: FastAPI依存注入でDBセッションを提供する
      設計概要: yieldでセッションを提供し、リクエスト完了後にcloseする
      呼び出し先設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
      呼び出し元設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN, DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
