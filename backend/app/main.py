"""
FastAPIアプリケーションのエントリーポイント。

要件トレーサビリティ:
  要件ID: RQ-DT-DB-REQUIRED
  設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
  要件概要: FastAPIアプリの初期化、ルーター登録、DB初期化を行う
  設計概要: アプリ起動時にcreate_all()でテーブルを作成し、シードデータを投入する。/api/プレフィックスでルーターを登録する
  呼び出し先設計ID: DS-FN-SEED-INITIAL-USER-FT-CREATE-USER, DS-FN-CONFIGURE-DB-NF-CONCURRENT-USERS
  呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import engine, SessionLocal
from app.models import Equipment, Loan, User
from app.db.database import Base
from app.db.seed import seed_initial_admin
from app.api.v1 import auth, equipment, loans, users

app = FastAPI(title="備品管理・貸出管理アプリ")

# CORSミドルウェア設定（フロントエンドからのリクエストを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルーター登録（/api/プレフィックス）
app.include_router(auth.router, prefix="/api")
app.include_router(equipment.router, prefix="/api")
app.include_router(loans.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.on_event("startup")
def startup_event():
    """
    アプリ起動時にDBテーブル作成とシードデータ投入を実行する。

    要件トレーサビリティ:
      要件ID: RQ-DT-DB-REQUIRED, RQ-FT-CREATE-USER
      設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED, DS-FN-SEED-INITIAL-USER-FT-CREATE-USER
      要件概要: アプリ起動時にDBを初期化し初期管理者アカウントを登録する
      設計概要: Base.metadata.create_all()でテーブルを作成後、seed_initial_admin()で管理者をシードする
      呼び出し先設計ID: DS-FN-SEED-INITIAL-USER-FT-CREATE-USER
      呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_initial_admin(db)
    finally:
        db.close()
