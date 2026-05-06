"""
FastAPI アプリケーションエントリーポイント

要件トレーサビリティ:
  要件ID: RQ-AT-WEB-GUI, RQ-AT-FRONTEND-BACKEND-SEPARATION, RQ-NF-ACCESS-CONTROL
  設計ID: DS-MD-BACKEND-APP-AT-WEB-GUI
  要件概要: Web GUIアプリケーションを提供し、フロントエンドとバックエンドを分離する
  設計概要: FastAPI アプリケーションを起動し、APIエンドポイントを公開する
  呼び出し先: DS-CL-AUTH-ROUTER-FT-LOGIN, DS-CL-ITEM-ROUTER-FT-REGISTER-ITEM, DS-CL-USER-ROUTER-FT-REGISTER-USER, DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
  呼び出し元: uvicorn (HTTPサーバー)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.routers import auth_router, item_router, user_router
from src.database.database_manager import db_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    アプリケーション起動時と終了時の処理
    
    要件ID: RQ-DT-INITIAL-ADMIN
    設計ID: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
    要件概要: アプリケーション起動時にデータベースを初期化する
    設計概要: データベース接続を確立し、テーブルを作成し、初期管理者を登録する
    呼び出し先: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
    """
    # 起動時: データベースを初期化
    db_manager.initialize()
    
    yield
    
    # 終了時: 特に処理なし


# FastAPIアプリケーションの作成
app = FastAPI(
    title="備品管理・貸出管理API",
    description="備品の登録・編集・削除、貸出・返却、利用者管理を行うAPI",
    version="1.0.0",
    lifespan=lifespan
)

# CORSミドルウェアの設定
# 要件ID: RQ-AT-FRONTEND-BACKEND-SEPARATION
# 設計ID: DS-MD-BACKEND-APP-AT-WEB-GUI
# 要件概要: フロントエンドとバックエンドを分離し、CORSを許可する
# 設計概要: Nginxリバースプロキシ経由でのアクセスを許可する
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの登録
# 要件ID: RQ-FT-LOGIN, RQ-FT-REGISTER-ITEM, RQ-FT-REGISTER-USER
# 設計ID: DS-MD-BACKEND-APP-AT-WEB-GUI
# 要件概要: 認証、備品管理、利用者管理のAPIエンドポイントを提供する
# 設計概要: 各機能のルーターを /api プレフィックスで登録する
app.include_router(auth_router.router, prefix="/api")
app.include_router(item_router.router, prefix="/api")
app.include_router(user_router.router, prefix="/api")


@app.get("/")
def root():
    """
    ルートエンドポイント（ヘルスチェック用）
    
    要件ID: RQ-NF-RESPONSE-TIME
    設計ID: DS-MD-BACKEND-APP-AT-WEB-GUI
    要件概要: APIサーバーの稼働状態を確認する
    設計概要: 簡単なヘルスチェックレスポンスを返す
    
    Returns:
        dict: ステータスメッセージ
    """
    return {"status": "ok", "message": "備品管理・貸出管理API"}
