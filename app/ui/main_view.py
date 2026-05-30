"""
備品一覧メイン画面モジュール。

要件ID: RQ-UI-ASSET-LIST-SCREEN
設計ID: DS-MD-STREAMLIT-UI-UI-ASSET-LIST-SCREEN
要件概要: 備品一覧、貸出/返却入力、ユーザー管理導線を提供する。
設計概要: 認証済みユーザーに応じて一覧画面と各ポップアップを描画する。
呼び出し先設計ID: DS-IF-ASSET-LIST-SCREEN-UI-ASSET-LIST-SCREEN, DS-IF-LOAN-POPUP-SCREEN-UI-LOAN-ENTRY-POPUP, DS-IF-RETURN-ENTRY-POPUP-FT-REGISTER-RETURN, DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
呼び出し元設計ID: DS-MD-APP-CORE-FT-VIEW-ASSET-STATUS
"""

from __future__ import annotations

import streamlit as st

from app.services.asset_service import AssetService
from app.services.loan_service import LoanService
from app.services.user_service import UserService
from app.ui.user_view import UserManagementView


class MainView:
    """
    備品一覧メイン画面を描画するクラス。

    要件ID: RQ-UI-ASSET-LIST-SCREEN
    設計ID: DS-IF-ASSET-LIST-SCREEN-UI-ASSET-LIST-SCREEN
    要件概要: 備品一覧の閲覧と管理担当者の更新操作を提供すること。
    設計概要: 一覧表示、貸出返却ポップアップ、ユーザー管理画面を統合表示する。
    呼び出し先設計ID: DS-CL-ASSET-SERVICE-FT-MANAGE-ASSET-MASTER, DS-CL-LOAN-SERVICE-FT-REGISTER-LOAN, DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
    呼び出し元設計ID: DS-MD-APP-CORE-FT-VIEW-ASSET-STATUS
    """

    def __init__(
        self,
        asset_service: AssetService,
        loan_service: LoanService,
        user_service: UserService,
        user_management_view: UserManagementView,
    ) -> None:
        """
        MainViewを初期化する。

        Args:
            asset_service (AssetService): 備品サービス。
            loan_service (LoanService): 貸出返却サービス。
            user_service (UserService): ユーザーサービス。
            user_management_view (UserManagementView): ユーザー管理画面。

        要件ID: RQ-UI-ASSET-LIST-SCREEN
        設計ID: DS-IF-ASSET-LIST-SCREEN-UI-ASSET-LIST-SCREEN
        要件概要: 備品一覧画面から必要な業務操作を呼び出せること。
        設計概要: 必要サービスと画面コンポーネントを保持する。
        呼び出し先設計ID: なし
        呼び出し元設計ID: DS-MD-APP-CORE-FT-VIEW-ASSET-STATUS
        """
        self.asset_service = asset_service
        self.loan_service = loan_service
        self.user_service = user_service
        self.user_management_view = user_management_view

    def _render_loan_popup(self, asset_id: int) -> None:
        """
        貸出入力ポップアップを描画する。

        Args:
            asset_id (int): 対象備品ID。

        要件ID: RQ-UI-LOAN-ENTRY-POPUP
        設計ID: DS-IF-LOAN-POPUP-SCREEN-UI-LOAN-ENTRY-POPUP
        要件概要: 貸出先と返却予定日を必須入力して貸出登録できること。
        設計概要: ポップオーバーで入力値を受け取り、サービスに処理を委譲する。
        呼び出し先設計ID: DS-FN-REGISTER-LOAN-FT-REGISTER-LOAN
        呼び出し元設計ID: DS-IF-ASSET-LIST-SCREEN-UI-ASSET-LIST-SCREEN
        """
        with st.popover(f"貸出_{asset_id}"):
            active_users = [user for user in self.user_service.list_users() if user.is_active]
            borrower_options = [""] + [user.display_name for user in active_users]
            borrower = st.selectbox(
                f"貸出先_{asset_id}",
                options=borrower_options,
                key=f"borrower_{asset_id}",
                format_func=lambda name: "選択してください" if name == "" else name,
            )
            due_date = st.text_input(f"返却予定日_{asset_id}(YYYY-MM-DD)", key=f"due_{asset_id}")
            if st.button("貸出確定", key=f"loan_submit_{asset_id}"):
                ok, message = self.loan_service.register_loan(asset_id, borrower, due_date)
                if not ok:
                    st.error(message)
                    return
                st.success(message)
                st.rerun()

    def _render_return_popup(self, asset_id: int) -> None:
        """
        返却入力ポップアップを描画する。

        Args:
            asset_id (int): 対象備品ID。

        要件ID: RQ-FT-REGISTER-RETURN
        設計ID: DS-IF-RETURN-ENTRY-POPUP-FT-REGISTER-RETURN
        要件概要: 返却日入力で返却登録を行えること。
        設計概要: ポップオーバーで返却日入力を受け、返却処理を実行する。
        呼び出し先設計ID: DS-FN-REGISTER-RETURN-FT-REGISTER-RETURN
        呼び出し元設計ID: DS-IF-ASSET-LIST-SCREEN-UI-ASSET-LIST-SCREEN
        """
        with st.popover(f"返却_{asset_id}"):
            returned_date = st.text_input(f"返却日_{asset_id}(YYYY-MM-DD)", value=self.loan_service.today(), key=f"return_{asset_id}")
            if st.button("返却確定", key=f"return_submit_{asset_id}"):
                ok, message = self.loan_service.register_return(asset_id, returned_date)
                if not ok:
                    st.error(message)
                    return
                st.success(message)
                st.rerun()

    def _render_asset_row(self, row: object, is_admin: bool) -> None:
        """
        備品一覧の1行を描画する。

        Args:
            row (object): 備品表示行。
            is_admin (bool): 管理担当者権限フラグ。

        要件ID: RQ-FT-VIEW-ASSET-STATUS
        設計ID: DS-IF-ASSET-LIST-SCREEN-UI-ASSET-LIST-SCREEN
        要件概要: 一覧で状態と貸出中利用者名を確認できること。
        設計概要: 備品情報を列表示し、管理権限時のみ貸出返却操作を提供する。
        呼び出し先設計ID: DS-IF-LOAN-POPUP-SCREEN-UI-LOAN-ENTRY-POPUP, DS-IF-RETURN-ENTRY-POPUP-FT-REGISTER-RETURN
        呼び出し元設計ID: DS-IF-ASSET-LIST-SCREEN-UI-ASSET-LIST-SCREEN
        """
        cols = st.columns([1, 2, 2, 1, 2, 2])
        cols[0].write(row.asset_code)
        cols[1].write(row.asset_name)
        cols[2].write(row.location)
        cols[3].write("利用可能" if row.status == "available" else "貸出中")
        cols[4].write(row.borrower_name or "-")

        with cols[5]:
            if is_admin and row.status == "available":
                self._render_loan_popup(row.asset_id)
            if is_admin and row.status == "loaned":
                self._render_return_popup(row.asset_id)

    def render(self) -> None:
        """
        メイン画面を描画する。

        要件ID: RQ-UI-ASSET-LIST-SCREEN
        設計ID: DS-IF-ASSET-LIST-SCREEN-UI-ASSET-LIST-SCREEN
        要件概要: 備品一覧閲覧と管理操作を提供すること。
        設計概要: 検索条件を受けて一覧を描画し、管理担当者には追加機能を表示する。
        呼び出し先設計ID: DS-FN-VIEW-ASSET-STATUS-FT-VIEW-ASSET-STATUS, DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
        呼び出し元設計ID: DS-MD-APP-CORE-FT-VIEW-ASSET-STATUS
        """
        current_user = st.session_state.get("current_user")
        is_admin = bool(current_user and current_user.role == "admin")

        def render_asset_list() -> None:
            st.title("備品一覧")
            keyword = st.text_input("検索条件")
            rows = self.asset_service.list_assets_with_status(keyword)

            head = st.columns([1, 2, 2, 1, 2, 2])
            head[0].write("管理番号")
            head[1].write("備品名")
            head[2].write("保管場所")
            head[3].write("状態")
            head[4].write("貸出中利用者")
            head[5].write("操作")

            for row in rows:
                self._render_asset_row(row, is_admin)

        if is_admin:
            tab_assets, tab_users = st.tabs(["備品一覧", "ユーザー管理"])
            with tab_assets:
                render_asset_list()
            with tab_users:
                self.user_management_view.render()
            return

        render_asset_list()
