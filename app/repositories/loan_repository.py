"""
貸出状態リポジトリモジュール。

要件ID: RQ-DT-LOAN-STATUS-ENTITY
設計ID: DS-CL-LOAN-REPOSITORY-DT-LOAN-STATUS-ENTITY
要件概要: 現在の貸出状態を保持し、返却時に利用可能へ戻せること。
設計概要: loan_statusテーブルの登録/更新を担い、返却済み履歴は保持しない運用を実装する。
呼び出し先設計ID: DS-SC-LOAN-STATUS-DT-LOAN-STATUS-ENTITY
呼び出し元設計ID: DS-CL-LOAN-SERVICE-FT-REGISTER-LOAN
"""

from __future__ import annotations

from datetime import datetime
from sqlite3 import Connection


class LoanRepository:
    """
    loan_statusテーブルのデータアクセスを提供するクラス。

    要件ID: RQ-DT-LOAN-STATUS-ENTITY
    設計ID: DS-CL-LOAN-REPOSITORY-DT-LOAN-STATUS-ENTITY
    要件概要: 備品の現在貸出状態を保持し一覧表示に反映できること。
    設計概要: 貸出時に上書き保存し、返却時に借用者情報をクリアする。
    呼び出し先設計ID: DS-SC-LOAN-STATUS-DT-LOAN-STATUS-ENTITY
    呼び出し元設計ID: DS-CL-LOAN-SERVICE-FT-REGISTER-LOAN
    """

    def __init__(self, conn: Connection) -> None:
        """
        リポジトリを初期化する。

        Args:
            conn (Connection): SQLite接続。

        要件ID: RQ-DT-LOAN-STATUS-ENTITY
        設計ID: DS-CL-LOAN-REPOSITORY-DT-LOAN-STATUS-ENTITY
        要件概要: 貸出状態データへの一貫したアクセスを提供する。
        設計概要: DB接続を保持して貸出更新処理で利用する。
        呼び出し先設計ID: なし
        呼び出し元設計ID: DS-CL-LOAN-SERVICE-FT-REGISTER-LOAN
        """
        self.conn = conn

    def upsert_loan(self, asset_id: int, borrower_name: str, due_date: str) -> None:
        """
        貸出状態を登録または更新する。

        Args:
            asset_id (int): 備品ID。
            borrower_name (str): 貸出先。
            due_date (str): 返却予定日。

        要件ID: RQ-FT-REGISTER-LOAN
        設計ID: DS-FN-REGISTER-LOAN-FT-REGISTER-LOAN
        要件概要: 貸出先と返却予定日を登録して貸出状態を更新する。
        設計概要: asset_id単位でUPSERTし、現在状態のみ保持する。
        呼び出し先設計ID: DS-SC-LOAN-STATUS-DT-LOAN-STATUS-ENTITY
        呼び出し元設計ID: DS-CL-LOAN-SERVICE-FT-REGISTER-LOAN
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute(
            """
            INSERT INTO loan_status (asset_id, borrower_name, due_date, loaned_at, returned_at)
            VALUES (?, ?, ?, ?, NULL)
            ON CONFLICT(asset_id) DO UPDATE SET
                borrower_name = excluded.borrower_name,
                due_date = excluded.due_date,
                loaned_at = excluded.loaned_at,
                returned_at = NULL
            """,
            (asset_id, borrower_name, due_date, now),
        )

    def mark_returned(self, asset_id: int, returned_date: str) -> None:
        """
        返却処理として貸出先情報をクリアする。

        Args:
            asset_id (int): 備品ID。
            returned_date (str): 返却日。

        要件ID: RQ-DT-DATA-RETENTION-POLICY
        設計ID: DS-SC-RETENTION-POLICY-DT-DATA-RETENTION-POLICY
        要件概要: 返却済み履歴を保持せず、現在状態のみ管理する。
        設計概要: 返却時に借用者・返却予定日をNULL化し、返却日時のみ一時更新して状態管理する。
        呼び出し先設計ID: DS-SC-LOAN-STATUS-DT-LOAN-STATUS-ENTITY
        呼び出し元設計ID: DS-CL-LOAN-SERVICE-FT-REGISTER-LOAN
        """
        self.conn.execute(
            """
            UPDATE loan_status
            SET borrower_name = NULL,
                due_date = NULL,
                returned_at = ?
            WHERE asset_id = ?
            """,
            (returned_date, asset_id),
        )
