"""
FastAPIアプリケーションエントリーポイントモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-LOGIN
  設計ID: DS-MD-BACKEND-FT-LIST-EQUIPMENT
  要件概要: 全機能（認証・備品管理・ユーザー管理）を提供するWebAPIアプリケーション。
  設計概要: FastAPIアプリを生成し、各ルーターを登録する。起動時にDBスキーマと初期管理者を自動生成する。
  呼び出し先設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN, DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT, DS-IF-LIST-USERS-FT-MANAGE-USERS
  呼び出し元設計ID: なし
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, SessionLocal
from app.api import auth, equipment, users


def seed_initial_admin():
    """
    初期管理者アカウントが存在しない場合に自動登録する。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-USERS
      設計ID: DS-FN-MANAGE-USERS-FT-MANAGE-USERS
      要件概要: 管理者がアプリ画面からユーザーを管理する。初回起動時は初期管理者が必要。
      設計概要: 起動時にusersテーブルのadminロールが0件の場合、INITIAL_ADMIN_PASSWORD環境変数を用いて登録する。
      呼び出し先設計ID: DS-FN-HASH-PASSWORD-NF-PASSWORD-HASH, DS-SC-USER-DT-ENTITY-USER
      呼び出し元設計ID: DS-MD-BACKEND-FT-LIST-EQUIPMENT
    """
    from app.models.user import User
    from app.core.security import hash_password

    db = SessionLocal()
    try:
        admin_count = db.query(User).filter(User.role == "admin").count()
        if admin_count == 0:
            initial_password = os.getenv("INITIAL_ADMIN_PASSWORD", "admin1234")
            admin = User(
                name="管理者",
                email="admin@example.com",
                password_hash=hash_password(initial_password),
                role="admin",
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    アプリケーションライフサイクル管理。起動時にDB初期化と初期管理者登録を行う。

    要件トレーサビリティ:
      要件ID: RQ-DT-DB-REQUIRED
      設計ID: DS-MD-SQLITE-DT-DB-REQUIRED
      要件概要: 起動時にDBスキーマを自動生成する。初期管理者が存在しない場合は自動登録する。
      設計概要: FastAPI lifespanでinit_db()とseed_initial_admin()を順次実行する。
      呼び出し先設計ID: DS-MD-SQLITE-DT-DB-REQUIRED, DS-FN-MANAGE-USERS-FT-MANAGE-USERS
      呼び出し元設計ID: なし
    """
    init_db()
    seed_initial_admin()
    yield


app = FastAPI(title="備品管理アプリ", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(equipment.router)
app.include_router(users.router)
