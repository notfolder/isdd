"""
ユーザー登録編集ポップアップモジュール。

要件ID: RQ-FT-MANAGE-USER-ACCOUNT
設計ID: DS-IF-USER-ENTRY-POPUP-FT-MANAGE-USER-ACCOUNT
要件概要: ユーザー登録と編集をポップアップで実行できること。
設計概要: 必須入力と重複エラーをポップアップ内に表示して保存可否を制御する。
呼び出し先設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USER-ACCOUNT, DS-FN-ERR-USER-DUPLICATE-FT-MANAGE-USER-ACCOUNT
呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
"""

from __future__ import annotations

import streamlit as st

from app.models.entities import UserAccount
from app.services.user_service import UserService


class UserEntryPopup:
    """
    ユーザー登録編集ポップアップを描画するクラス。

    要件ID: RQ-FT-MANAGE-USER-ACCOUNT
    設計ID: DS-IF-USER-ENTRY-POPUP-FT-MANAGE-USER-ACCOUNT
    要件概要: ユーザー登録・編集の入力をモーダルで完結できること。
    設計概要: Streamlitダイアログで入力を受け、保存結果を画面へ返す。
    呼び出し先設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USER-ACCOUNT
    呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
    """

    def __init__(self, user_service: UserService) -> None:
        """
        UserEntryPopupを初期化する。

        Args:
            user_service (UserService): ユーザーサービス。

        要件ID: RQ-FT-MANAGE-USER-ACCOUNT
        設計ID: DS-IF-USER-ENTRY-POPUP-FT-MANAGE-USER-ACCOUNT
        要件概要: ユーザー保存処理をポップアップから呼び出せること。
        設計概要: サービス依存を保持する。
        呼び出し先設計ID: なし
        呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
        """
        self.user_service = user_service

    def render(self, user: UserAccount | None = None, key_suffix: str = "new") -> None:
        """
        ユーザー登録/編集ポップアップを表示する。

        Args:
            user (UserAccount | None): 編集対象ユーザー。

        要件ID: RQ-FT-MANAGE-USER-ACCOUNT
        設計ID: DS-IF-USER-ENTRY-POPUP-FT-MANAGE-USER-ACCOUNT
        要件概要: 氏名、ログインID、パスワード、権限、有効状態を入力して保存できること。
        設計概要: 入力値をサービスへ渡し、成功時は画面を再描画する。
        呼び出し先設計ID: DS-FN-MANAGE-USER-ACCOUNT-FT-MANAGE-USER-ACCOUNT
        呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
        """
        title = "ユーザー編集" if user else "新規ユーザー登録"
        with st.popover(title):
            display_name = st.text_input("氏名", value=user.display_name if user else "", key=f"name_{key_suffix}")
            login_id = st.text_input("ログインID", value=user.login_id if user else "", key=f"login_{key_suffix}")
            password = st.text_input("パスワード", type="password", key=f"pass_{key_suffix}")
            role = st.selectbox(
                "権限",
                ["admin", "viewer"],
                index=0 if (user is None or user.role == "admin") else 1,
                key=f"role_{key_suffix}",
            )
            is_active = st.checkbox("有効", value=user.is_active if user else True, key=f"active_{key_suffix}")
            if st.button("確定", key=f"save_{key_suffix}"):
                ok, message = self.user_service.save_user_account(
                    user_id=user.user_id if user else 0,
                    display_name=display_name,
                    login_id=login_id,
                    raw_password=password,
                    role=role,
                    is_active=is_active,
                )
                if not ok:
                    st.error(message)
                    return
                st.success(message)
                st.rerun()
