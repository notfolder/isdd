"""
FastAPI アプリケーション起動モジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-UNIFY-ASSET-LEDGER
  設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
  要件概要: 備品管理・貸出管理 API をバックエンドとして提供する。
  設計概要: ログ設定、DB初期化、各ルーター登録を行ってアプリを起動する。
  呼び出し先設計ID: DS-MD-NGINX-API-PATH-FT-UNIFY-ASSET-LEDGER
  呼び出し元設計ID: DS-MD-STANDALONE-DEPLOYMENT-EX-NO-EXTERNAL-INTEGRATION
"""

from __future__ import annotations

from fastapi import FastAPI

from .api.dependencies import get_gateway
from .api.routers.assets_router import router as assets_router
from .api.routers.auth_router import router as auth_router
from .api.routers.health_router import router as health_router
from .api.routers.users_router import router as users_router
from .config.logging import setup_logging
from .services.user_service import UserService


def _seed_default_users_if_empty(gateway) -> None:
    """
    users テーブルが空の場合のみ初期ユーザーを投入する。

    要件トレーサビリティ:
      要件ID: RQ-TS-VERIFY-LOGIN-ROLE-ROUTING
      設計ID: DS-FN-SAVE-USER-FT-MANAGE-USERS
      要件概要: 管理者と一般利用者のアカウントが存在する前提でログイン検証を行う。
      設計概要: users 件数が 0 のときだけ admin/viewer を登録する。
      呼び出し先設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USERS
      呼び出し元設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
    """
    user_service = UserService(gateway)
    admin_row = gateway.fetch_one("SELECT login_id FROM users WHERE login_id = ?", ("admin",))
    if admin_row is None:
      user_service.save_user("admin", "管理者", "admin123", "admin")

    viewer_row = gateway.fetch_one("SELECT login_id FROM users WHERE login_id = ?", ("viewer",))
    if viewer_row is None:
      user_service.save_user("viewer", "一般利用者", "viewer123", "viewer")


def create_app() -> FastAPI:
    """
    FastAPI アプリを生成して初期化する。

    要件トレーサビリティ:
      要件ID: RQ-EX-NO-EXTERNAL-INTEGRATION
      設計ID: DS-FN-LIST-ASSETS-FT-MANAGE-ASSET-MASTER
      要件概要: 外部依存なしで単体起動できる必要がある。
      設計概要: ローカル DB 初期化後に API ルーターを登録する。
      呼び出し先設計ID: DS-SC-LOCAL-DB-SCHEMA-DT-USE-INTERNAL-DB, DS-IF-APPLICATION-LOG-OP-APPLICATION-LOG-RETENTION
      呼び出し元設計ID: DS-MD-FASTAPI-BACKEND-FT-UNIFY-ASSET-LEDGER
    """
    setup_logging()
    gateway = get_gateway()
    gateway.initialize_schema()
    _seed_default_users_if_empty(gateway)

    app = FastAPI(title="Asset Lending Management API")
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(assets_router)
    app.include_router(users_router)
    return app


app = create_app()
