"""
FastAPI アプリケーションエントリーポイント。

要件トレーサビリティ:
  要件ID: RQ-FT-LOGIN, RQ-OP-INITIAL-ADMIN-ENV
  設計ID: DS-MD-BACKEND-FT-MANAGE-EQUIPMENT
  要件概要: バックエンドAPIサーバーとして全機能を提供する。起動時にDBを初期化し初期管理者を作成する。
  設計概要: FastAPIアプリを初期化し、lifespan内でcreate_allとinitialize_adminを実行する。全Routerを登録する。
  呼び出し先: DS-MD-DATABASE-DT-EQUIPMENT-ENTITY, DS-FN-INIT-ADMIN-OP-INITIAL-ADMIN-ENV
  呼び出し元: uvicorn
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import engine, Base, SessionLocal
from app.models import equipment, user, loan_state
from app.api import auth, users, equipment as equipment_router
from app.services.user_service import UserService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    アプリ起動・終了ライフサイクル管理。

    要件トレーサビリティ:
      要件ID: RQ-OP-INITIAL-ADMIN-ENV
      設計ID: DS-FN-INIT-ADMIN-OP-INITIAL-ADMIN-ENV
      要件概要: 起動時にDBスキーマを作成し、user テーブルが空の場合のみ初期管理者を作成する。
      設計概要: Base.metadata.create_all でテーブルを作成後、UserService.initialize_admin を呼び出す。
      呼び出し先: DS-MD-DATABASE-DT-EQUIPMENT-ENTITY, DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
      呼び出し元: FastAPI lifespan
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        UserService(db).initialize_admin()
    finally:
        db.close()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(equipment_router.router)
