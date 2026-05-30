"""
ログイン画面モジュール。

要件ID: RQ-UI-LOGIN-SCREEN
設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN
要件概要: ログインIDとパスワードで認証し、権限に応じた利用を可能にする。
設計概要: ログインフォームとエラー表示を提供し、認証サービスへ入力を渡す。
呼び出し先設計ID: DS-CL-AUTH-SERVICE-FT-AUTHENTICATE-USER
呼び出し元設計ID: DS-MD-STREAMLIT-UI-UI-ASSET-LIST-SCREEN
"""

from __future__ import annotations

import streamlit as st

from app.services.auth_service import AuthService


class LoginView:
    """
    ログイン画面を描画するビュークラス。

    要件ID: RQ-UI-LOGIN-SCREEN
    設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN
    要件概要: 認証失敗時にエラーを表示し、成功時に画面遷移できること。
    設計概要: Streamlitフォームで認証入力を受け、session_stateへ結果を設定する。
    呼び出し先設計ID: DS-CL-AUTH-SERVICE-FT-AUTHENTICATE-USER
    呼び出し元設計ID: DS-MD-STREAMLIT-UI-UI-ASSET-LIST-SCREEN
    """

    def __init__(self, auth_service: AuthService) -> None:
        """
        LoginViewを初期化する。

        Args:
            auth_service (AuthService): 認証サービス。

        要件ID: RQ-UI-LOGIN-SCREEN
        設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN
        要件概要: ログイン画面から認証機能を利用できること。
        設計概要: 認証サービス依存を保持する。
        呼び出し先設計ID: なし
        呼び出し元設計ID: DS-MD-STREAMLIT-UI-UI-ASSET-LIST-SCREEN
        """
        self.auth_service = auth_service

    def render(self) -> None:
        """
        ログイン画面を描画して認証処理を実行する。

        要件ID: RQ-UI-LOGIN-SCREEN
        設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN
        要件概要: ログイン画面に入力欄、ボタン、エラー表示を提供する。
        設計概要: フォーム送信時にauthenticate_userを呼び出し、結果をsession_stateに保存する。
        呼び出し先設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
        呼び出し元設計ID: DS-MD-STREAMLIT-UI-UI-ASSET-LIST-SCREEN
        """
        st.title("備品管理システム")
        login_id = st.text_input("ログインID")
        password = st.text_input("パスワード", type="password")
        if st.button("ログイン"):
            user = self.auth_service.authenticate_user(login_id, password)
            if user is None:
                st.error("IDまたはパスワードが正しくないか、無効なアカウントです。")
                return
            st.session_state["is_authenticated"] = True
            st.session_state["current_user"] = user
            st.rerun()
