"""
バックエンドテスト共通フィクスチャ。

要件トレーサビリティ:
  要件ID: RQ-FT-MAKE-RESERVATION, RQ-FT-CANCEL-RESERVATION, RQ-FT-FETCH-DEPT-BY-LOGIN-ID
  設計ID: DS-FN-TEST-RESERVATION-CREATE-FT-MAKE-RESERVATION, DS-FN-TEST-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID
  要件概要: バックエンドテスト用の SQLite インメモリDB・TestClient を提供する。
  設計概要: SQLite インメモリDBでテーブルを作成し、テスト間でDBを初期化する。
  呼び出し先: なし
  呼び出し元: pytest
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("MOCK_EXTERNAL_DB", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("INITIAL_ADMIN_LOGIN_ID", "admin")
os.environ.setdefault("INITIAL_ADMIN_PASSWORD", "changeme")

from app.core.database import Base, get_db
from app.main import app

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def admin_client(client):
    """管理者でログインした TestClient を返す。"""
    from app.services.user_service import UserService
    db = TestingSessionLocal()
    try:
        UserService(db).initialize_admin()
    finally:
        db.close()

    admin_id = os.environ.get("INITIAL_ADMIN_LOGIN_ID", "admin")
    admin_pw = os.environ.get("INITIAL_ADMIN_PASSWORD", "changeme")
    client.post("/api/auth/login", json={"login_id": admin_id, "password": admin_pw})
    return client
