"""
アプリケーションエントリポイント。

要件ID: RQ-FT-VIEW-ASSET-STATUS
設計ID: DS-MD-APP-CORE-FT-VIEW-ASSET-STATUS
要件概要: ログイン後に備品一覧および管理機能へ遷移できること。
設計概要: DB初期化、サービス生成、画面描画の起点を提供する。
呼び出し先設計ID: DS-SC-SQLITE-SCHEMA-DT-DB-NECESSITY, DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN, DS-IF-ASSET-LIST-SCREEN-UI-ASSET-LIST-SCREEN
呼び出し元設計ID: なし
"""

from __future__ import annotations

import streamlit as st

from app.db.connection import get_connection
from app.db.schema import initialize_schema
from app.repositories.asset_repository import AssetRepository
from app.repositories.loan_repository import LoanRepository
from app.repositories.user_repository import UserRepository
from app.services.asset_service import AssetService
from app.services.auth_service import AuthService
from app.services.loan_service import LoanService
from app.services.user_service import UserService
from app.ui.login_view import LoginView
from app.ui.main_view import MainView
from app.ui.user_view import UserManagementView


def _bootstrap() -> tuple[LoginView, MainView]:
    """
    依存オブジェクトを初期化する。

    Returns:
        tuple[LoginView, MainView]: ログイン画面とメイン画面。

    要件ID: RQ-DT-DB-NECESSITY
    設計ID: DS-MD-STREAMLIT-UI-UI-ASSET-LIST-SCREEN
    要件概要: 内部DBを初期化し、アプリ起動時に利用可能な状態にすること。
    設計概要: 接続、スキーマ、リポジトリ、サービス、ビューを順に組み立てる。
    呼び出し先設計ID: DS-SC-SQLITE-SCHEMA-DT-DB-NECESSITY, DS-CL-AUTH-SERVICE-FT-AUTHENTICATE-USER, DS-CL-ASSET-SERVICE-FT-MANAGE-ASSET-MASTER, DS-CL-LOAN-SERVICE-FT-REGISTER-LOAN, DS-CL-USER-SERVICE-FT-MANAGE-USER-ACCOUNT
    呼び出し元設計ID: DS-MD-APP-CORE-FT-VIEW-ASSET-STATUS
    """
    conn = get_connection()
    initialize_schema(conn)

    user_repository = UserRepository(conn)
    asset_repository = AssetRepository(conn)
    loan_repository = LoanRepository(conn)

    auth_service = AuthService(user_repository)
    asset_service = AssetService(asset_repository)
    loan_service = LoanService(conn, asset_repository, loan_repository)
    user_service = UserService(user_repository)

    user_view = UserManagementView(user_service)
    main_view = MainView(asset_service, loan_service, user_service, user_view)
    login_view = LoginView(auth_service)
    return login_view, main_view


def main() -> None:
    """
    Streamlitアプリを起動する。

    要件ID: RQ-UI-LOGIN-SCREEN
    設計ID: DS-MD-STREAMLIT-UI-UI-ASSET-LIST-SCREEN
    要件概要: 未認証時はログイン画面、認証後は備品一覧画面を表示すること。
    設計概要: session_stateの認証状態で描画するビューを切り替える。
    呼び出し先設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN, DS-IF-ASSET-LIST-SCREEN-UI-ASSET-LIST-SCREEN
    呼び出し元設計ID: DS-MD-APP-CORE-FT-VIEW-ASSET-STATUS
    """
    st.set_page_config(page_title="備品管理", layout="wide")
    if "is_authenticated" not in st.session_state:
        st.session_state["is_authenticated"] = False

    login_view, main_view = _bootstrap()

    if not st.session_state.get("is_authenticated", False):
        login_view.render()
        return

    if st.button("ログアウト"):
        st.session_state["is_authenticated"] = False
        st.session_state["current_user"] = None
        st.rerun()

    main_view.render()


if __name__ == "__main__":
    """
    スクリプト実行時にmainを呼び出す。

    要件ID: RQ-FT-VIEW-ASSET-STATUS
    設計ID: DS-MD-APP-CORE-FT-VIEW-ASSET-STATUS
    要件概要: アプリケーションを実行可能にすること。
    設計概要: 直接実行時のエントリポイントを提供する。
    呼び出し先設計ID: DS-MD-STREAMLIT-UI-UI-ASSET-LIST-SCREEN
    呼び出し元設計ID: なし
    """
    main()
