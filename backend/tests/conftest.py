"""
テスト設定・フィクスチャ。

要件トレーサビリティ:
  要件ID: RQ-DT-DB-REQUIRED
  設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
  要件概要: テスト用DBセッションとFastAPIテストクライアントを提供する
  設計概要: インメモリSQLiteを使用したテスト用エンジン・セッション・クライアントをフィクスチャとして定義する
  呼び出し先設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
  呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db.database import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """
    テスト用DBセッションフィクスチャ。

    要件トレーサビリティ:
      要件ID: RQ-DT-DB-REQUIRED
      設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
      要件概要: テスト用インメモリSQLiteセッションを提供する
      設計概要: 各テスト関数ごとにテーブルを作成・削除する
      呼び出し先設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
      呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """
    テスト用FastAPIクライアントフィクスチャ。

    要件トレーサビリティ:
      要件ID: RQ-DT-DB-REQUIRED
      設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
      要件概要: テスト用FastAPIクライアントを提供する
      設計概要: テスト用DBセッションをDI上書きしてTestClientを作成する
      呼び出し先設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
      呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
