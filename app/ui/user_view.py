"""
ユーザー管理画面モジュール。

要件ID: RQ-UI-USER-MANAGEMENT-SCREEN
設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
要件概要: ユーザー一覧と登録編集導線を提供する。
設計概要: 一覧表示と新規/編集ポップアップ呼び出しを行う。
呼び出し先設計ID: DS-IF-USER-ENTRY-POPUP-FT-MANAGE-USER-ACCOUNT, DS-FN-MANAGE-USER-ACCOUNT-FT-MANAGE-USER-ACCOUNT
呼び出し元設計ID: DS-MD-STREAMLIT-UI-UI-ASSET-LIST-SCREEN
"""

from __future__ import annotations

import streamlit as st

from app.models.entities import UserAccount
from app.services.user_service import UserService
from app.ui.user_popup import UserEntryPopup


class UserManagementView:
    """
    ユーザー管理画面を描画するクラス。

    要件ID: RQ-UI-USER-MANAGEMENT-SCREEN
    設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
    要件概要: ユーザー一覧確認と登録編集の操作を提供すること。
    設計概要: 一覧表示とポップアップ呼び出しを統合する。
    呼び出し先設計ID: DS-IF-USER-ENTRY-POPUP-FT-MANAGE-USER-ACCOUNT
    呼び出し元設計ID: DS-IF-ASSET-LIST-SCREEN-UI-ASSET-LIST-SCREEN
    """

    def __init__(self, user_service: UserService) -> None:
        """
        UserManagementViewを初期化する。

        Args:
            user_service (UserService): ユーザーサービス。

        要件ID: RQ-UI-USER-MANAGEMENT-SCREEN
        設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
        要件概要: ユーザー管理画面で保存処理を実行できること。
        設計概要: サービスとポップアップを保持する。
        呼び出し先設計ID: DS-IF-USER-ENTRY-POPUP-FT-MANAGE-USER-ACCOUNT
        呼び出し元設計ID: DS-MD-STREAMLIT-UI-UI-ASSET-LIST-SCREEN
        """
        self.user_service = user_service
        self.popup = UserEntryPopup(user_service)

    def _render_user_row(self, user: UserAccount) -> None:
        """
        1ユーザー行の操作UIを描画する。

        Args:
            user (UserAccount): 描画対象ユーザー。

        要件ID: RQ-FT-MANAGE-USER-ACCOUNT
        設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
        要件概要: ユーザーの編集と有効無効切替を実行できること。
        設計概要: 編集ポップアップと有効状態更新を行う。
        呼び出し先設計ID: DS-IF-USER-ENTRY-POPUP-FT-MANAGE-USER-ACCOUNT, DS-FN-MANAGE-USER-ACCOUNT-FT-MANAGE-USER-ACCOUNT
        呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
        """
        cols = st.columns([2, 2, 1, 1, 2])
        cols[0].write(user.display_name)
        cols[1].write(user.login_id)
        cols[2].write("管理担当者" if user.role == "admin" else "一般利用者")
        cols[3].write("有効" if user.is_active else "無効")
        with cols[4]:
            self.popup.render(user, key_suffix=f"edit_{user.user_id}")
            if st.button("有効/無効切替", key=f"toggle_{user.user_id}"):
                ok, message = self.user_service.save_user_account(
                    user_id=user.user_id,
                    display_name=user.display_name,
                    login_id=user.login_id,
                    raw_password="",
                    role=user.role,
                    is_active=not user.is_active,
                )
                if not ok:
                    st.error(message)
                    return
                st.success(message)
                st.rerun()

    def render(self) -> None:
        """
        ユーザー管理画面を描画する。

        要件ID: RQ-UI-USER-MANAGEMENT-SCREEN
        設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
        要件概要: ユーザー一覧と登録編集機能を提供すること。
        設計概要: 新規登録ポップアップと一覧行操作を表示する。
        呼び出し先設計ID: DS-IF-USER-ENTRY-POPUP-FT-MANAGE-USER-ACCOUNT, DS-FN-MANAGE-USER-ACCOUNT-FT-MANAGE-USER-ACCOUNT
        呼び出し元設計ID: DS-IF-ASSET-LIST-SCREEN-UI-ASSET-LIST-SCREEN
        """
        st.subheader("ユーザー管理")
        self.popup.render(None, key_suffix="new_user")
        users = self.user_service.list_users()
        st.markdown("---")
        head = st.columns([2, 2, 1, 1, 2])
        head[0].write("氏名")
        head[1].write("ログインID")
        head[2].write("権限")
        head[3].write("有効状態")
        head[4].write("操作")
        for user in users:
            self._render_user_row(user)
