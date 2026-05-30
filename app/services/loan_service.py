"""
貸出返却サービスモジュール。

要件ID: RQ-FT-REGISTER-LOAN
設計ID: DS-CL-LOAN-SERVICE-FT-REGISTER-LOAN
要件概要: 貸出登録と返却登録で備品状態を正しく遷移させる。
設計概要: 入力バリデーション、楽観排他、トランザクション境界を適用して更新する。
呼び出し先設計ID: DS-CL-ASSET-REPOSITORY-DT-ASSET-ENTITY, DS-CL-LOAN-REPOSITORY-DT-LOAN-STATUS-ENTITY, DS-FN-LOAN-TX-BOUNDARY-FT-REGISTER-LOAN, DS-FN-RETURN-TX-BOUNDARY-FT-REGISTER-RETURN
呼び出し元設計ID: DS-IF-LOAN-POPUP-SCREEN-UI-LOAN-ENTRY-POPUP, DS-IF-RETURN-ENTRY-POPUP-FT-REGISTER-RETURN
"""

from __future__ import annotations

from datetime import datetime
from sqlite3 import Connection

from app.repositories.asset_repository import AssetRepository
from app.repositories.loan_repository import LoanRepository


class LoanService:
    """
    貸出返却処理を提供するサービスクラス。

    要件ID: RQ-FT-REGISTER-LOAN
    設計ID: DS-CL-LOAN-SERVICE-FT-REGISTER-LOAN
    要件概要: 貸出先と返却予定日を登録して貸出状態を更新すること。
    設計概要: 入力検証後にloan_statusとassetsを同一トランザクションで更新する。
    呼び出し先設計ID: DS-CL-ASSET-REPOSITORY-DT-ASSET-ENTITY, DS-CL-LOAN-REPOSITORY-DT-LOAN-STATUS-ENTITY
    呼び出し元設計ID: DS-IF-LOAN-POPUP-SCREEN-UI-LOAN-ENTRY-POPUP, DS-IF-RETURN-ENTRY-POPUP-FT-REGISTER-RETURN
    """

    def __init__(self, conn: Connection, asset_repository: AssetRepository, loan_repository: LoanRepository) -> None:
        """
        LoanServiceを初期化する。

        Args:
            conn (Connection): SQLite接続。
            asset_repository (AssetRepository): 備品リポジトリ。
            loan_repository (LoanRepository): 貸出状態リポジトリ。

        要件ID: RQ-FT-REGISTER-LOAN
        設計ID: DS-CL-LOAN-SERVICE-FT-REGISTER-LOAN
        要件概要: 貸出返却処理を一貫して実行できること。
        設計概要: 必要なリポジトリと接続を保持する。
        呼び出し先設計ID: なし
        呼び出し元設計ID: DS-MD-STREAMLIT-UI-UI-ASSET-LIST-SCREEN
        """
        self.conn = conn
        self.asset_repository = asset_repository
        self.loan_repository = loan_repository

    def register_loan(self, asset_id: int, borrower_name: str, due_date: str) -> tuple[bool, str]:
        """
        貸出登録を実行する。

        Args:
            asset_id (int): 備品ID。
            borrower_name (str): 貸出先。
            due_date (str): 返却予定日。

        Returns:
            tuple[bool, str]: 成否とメッセージ。

        要件ID: RQ-FT-REGISTER-LOAN
        設計ID: DS-FN-REGISTER-LOAN-FT-REGISTER-LOAN
        要件概要: 貸出ボタン押下時に貸出先と返却予定日の入力を必須とすること。
        設計概要: 入力検証後にトランザクションでloan_statusとassetsを更新し、競合時は失敗を返す。
        呼び出し先設計ID: DS-FN-ERR-LOAN-REQUIRED-UI-LOAN-ENTRY-POPUP, DS-FN-LOAN-TX-BOUNDARY-FT-REGISTER-LOAN, DS-FN-ASSET-OPTIMISTIC-LOCK-FT-REGISTER-LOAN
        呼び出し元設計ID: DS-IF-LOAN-POPUP-SCREEN-UI-LOAN-ENTRY-POPUP
        """
        if not borrower_name or not due_date:
            return False, "貸出先と返却予定日は必須です。"

        target = self.asset_repository.get_asset(asset_id)
        if target is None:
            return False, "対象備品が見つかりません。"
        if target.status == "loaned":
            return False, "対象備品はすでに貸出中です。"

        try:
            self.conn.execute("BEGIN")
            self.loan_repository.upsert_loan(asset_id, borrower_name, due_date)
            updated = self.asset_repository.update_status_with_version(asset_id, "loaned", target.version_no)
            if not updated:
                self.conn.execute("ROLLBACK")
                return False, "他の更新と競合しました。画面を再読み込みしてください。"
            self.conn.commit()
            return True, "貸出登録が完了しました。"
        except Exception:
            self.conn.execute("ROLLBACK")
            return False, "貸出登録に失敗しました。"

    def register_return(self, asset_id: int, returned_date: str) -> tuple[bool, str]:
        """
        返却登録を実行する。

        Args:
            asset_id (int): 備品ID。
            returned_date (str): 返却日。

        Returns:
            tuple[bool, str]: 成否とメッセージ。

        要件ID: RQ-FT-REGISTER-RETURN
        設計ID: DS-FN-REGISTER-RETURN-FT-REGISTER-RETURN
        要件概要: 返却登録により利用可能状態へ戻せること。
        設計概要: 返却日必須を検証後、トランザクションでloan_statusとassetsを更新する。
        呼び出し先設計ID: DS-FN-ERR-RETURN-REQUIRED-FT-REGISTER-RETURN, DS-FN-RETURN-TX-BOUNDARY-FT-REGISTER-RETURN, DS-FN-ASSET-OPTIMISTIC-LOCK-FT-REGISTER-RETURN
        呼び出し元設計ID: DS-IF-RETURN-ENTRY-POPUP-FT-REGISTER-RETURN
        """
        if not returned_date:
            return False, "返却日は必須です。"

        target = self.asset_repository.get_asset(asset_id)
        if target is None:
            return False, "対象備品が見つかりません。"
        if target.status == "available":
            return False, "対象備品は返却済みです。"

        try:
            self.conn.execute("BEGIN")
            self.loan_repository.mark_returned(asset_id, returned_date)
            updated = self.asset_repository.update_status_with_version(asset_id, "available", target.version_no)
            if not updated:
                self.conn.execute("ROLLBACK")
                return False, "他の更新と競合しました。画面を再読み込みしてください。"
            self.conn.commit()
            return True, "返却登録が完了しました。"
        except Exception:
            self.conn.execute("ROLLBACK")
            return False, "返却登録に失敗しました。"

    def today(self) -> str:
        """
        当日の日付文字列を返す。

        Returns:
            str: YYYY-MM-DD形式の日付。

        要件ID: RQ-FT-REGISTER-RETURN
        設計ID: DS-IF-RETURN-ENTRY-POPUP-FT-REGISTER-RETURN
        要件概要: 返却日入力を行えること。
        設計概要: UI初期値として当日を提供する。
        呼び出し先設計ID: なし
        呼び出し元設計ID: DS-IF-RETURN-ENTRY-POPUP-FT-REGISTER-RETURN
        """
        return datetime.now().strftime("%Y-%m-%d")
