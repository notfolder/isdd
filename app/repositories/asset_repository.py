"""
備品リポジトリモジュール。

要件ID: RQ-DT-ASSET-ENTITY
設計ID: DS-CL-ASSET-REPOSITORY-DT-ASSET-ENTITY
要件概要: 備品マスタの登録、更新、一覧表示を行えること。
設計概要: assetsとloan_statusの結合参照、備品更新を提供する。
呼び出し先設計ID: DS-SC-ASSETS-DT-ASSET-ENTITY, DS-SC-LOAN-STATUS-DT-LOAN-STATUS-ENTITY
呼び出し元設計ID: DS-CL-ASSET-SERVICE-FT-MANAGE-ASSET-MASTER, DS-CL-LOAN-SERVICE-FT-REGISTER-LOAN
"""

from __future__ import annotations

from sqlite3 import Connection

from app.models.entities import Asset, AssetStatusView


class AssetRepository:
    """
    assetsテーブルのデータアクセスを提供するクラス。

    要件ID: RQ-DT-ASSET-ENTITY
    設計ID: DS-CL-ASSET-REPOSITORY-DT-ASSET-ENTITY
    要件概要: 備品台帳を更新し、状態を確認できること。
    設計概要: 備品一覧取得と備品属性更新、状態更新を担う。
    呼び出し先設計ID: DS-SC-ASSETS-DT-ASSET-ENTITY
    呼び出し元設計ID: DS-CL-ASSET-SERVICE-FT-MANAGE-ASSET-MASTER, DS-CL-LOAN-SERVICE-FT-REGISTER-LOAN
    """

    def __init__(self, conn: Connection) -> None:
        """
        リポジトリを初期化する。

        Args:
            conn (Connection): SQLite接続。

        要件ID: RQ-DT-ASSET-ENTITY
        設計ID: DS-CL-ASSET-REPOSITORY-DT-ASSET-ENTITY
        要件概要: 備品データを永続管理すること。
        設計概要: DB接続を保持する。
        呼び出し先設計ID: なし
        呼び出し元設計ID: DS-CL-ASSET-SERVICE-FT-MANAGE-ASSET-MASTER, DS-CL-LOAN-SERVICE-FT-REGISTER-LOAN
        """
        self.conn = conn

    def list_assets_with_status(self, keyword: str = "") -> list[AssetStatusView]:
        """
        備品一覧と貸出状態を取得する。

        Args:
            keyword (str): 検索キーワード。

        Returns:
            list[AssetStatusView]: 表示用備品一覧。

        要件ID: RQ-FT-VIEW-ASSET-STATUS
        設計ID: DS-FN-VIEW-ASSET-STATUS-FT-VIEW-ASSET-STATUS
        要件概要: 備品状態と貸出中利用者名を一覧で確認できること。
        設計概要: assetsとloan_statusを結合し、キーワードで絞り込む。
        呼び出し先設計ID: DS-SC-ASSETS-DT-ASSET-ENTITY, DS-SC-LOAN-STATUS-DT-LOAN-STATUS-ENTITY
        呼び出し元設計ID: DS-CL-ASSET-SERVICE-FT-MANAGE-ASSET-MASTER
        """
        like_keyword = f"%{keyword}%"
        rows = self.conn.execute(
            """
            SELECT a.asset_id, a.asset_code, a.asset_name, a.location, a.status, a.version_no,
                   l.borrower_name, l.due_date
            FROM assets a
            LEFT JOIN loan_status l ON l.asset_id = a.asset_id
            WHERE a.asset_name LIKE ? OR a.asset_code LIKE ? OR a.status LIKE ?
            ORDER BY a.asset_id
            """,
            (like_keyword, like_keyword, like_keyword),
        ).fetchall()
        return [
            AssetStatusView(
                asset_id=row["asset_id"],
                asset_code=row["asset_code"],
                asset_name=row["asset_name"],
                location=row["location"],
                status=row["status"],
                borrower_name=row["borrower_name"],
                due_date=row["due_date"],
                version_no=row["version_no"],
            )
            for row in rows
        ]

    def save_asset(self, asset: Asset) -> None:
        """
        備品を登録または更新する。

        Args:
            asset (Asset): 保存対象備品。

        要件ID: RQ-FT-MANAGE-ASSET-MASTER
        設計ID: DS-FN-MANAGE-ASSET-MASTER-FT-MANAGE-ASSET-MASTER
        要件概要: 備品の新規登録と更新を管理担当者が実行できること。
        設計概要: asset_idの有無でINSERT/UPDATEを切り替える。
        呼び出し先設計ID: DS-SC-ASSETS-DT-ASSET-ENTITY
        呼び出し元設計ID: DS-CL-ASSET-SERVICE-FT-MANAGE-ASSET-MASTER
        """
        if asset.asset_id == 0:
            self.conn.execute(
                """
                INSERT INTO assets (asset_code, asset_name, location, status, version_no)
                VALUES (?, ?, ?, ?, ?)
                """,
                (asset.asset_code, asset.asset_name, asset.location, asset.status, asset.version_no),
            )
        else:
            self.conn.execute(
                """
                UPDATE assets
                SET asset_code = ?, asset_name = ?, location = ?, status = ?, version_no = version_no + 1
                WHERE asset_id = ?
                """,
                (asset.asset_code, asset.asset_name, asset.location, asset.status, asset.asset_id),
            )
        self.conn.commit()

    def get_asset(self, asset_id: int) -> Asset | None:
        """
        備品IDで備品を取得する。

        Args:
            asset_id (int): 備品ID。

        Returns:
            Asset | None: 備品情報。

        要件ID: RQ-FT-REGISTER-LOAN
        設計ID: DS-FN-REGISTER-LOAN-FT-REGISTER-LOAN
        要件概要: 貸出登録時に対象備品の現状態を確認できること。
        設計概要: 貸出可否判定に必要な備品データを読み出す。
        呼び出し先設計ID: DS-SC-ASSETS-DT-ASSET-ENTITY
        呼び出し元設計ID: DS-CL-LOAN-SERVICE-FT-REGISTER-LOAN
        """
        row = self.conn.execute(
            """
            SELECT asset_id, asset_code, asset_name, location, status, version_no
            FROM assets
            WHERE asset_id = ?
            """,
            (asset_id,),
        ).fetchone()
        if row is None:
            return None
        return Asset(
            asset_id=row["asset_id"],
            asset_code=row["asset_code"],
            asset_name=row["asset_name"],
            location=row["location"],
            status=row["status"],
            version_no=row["version_no"],
        )

    def update_status_with_version(self, asset_id: int, status: str, version_no: int) -> bool:
        """
        version_noを条件に備品状態を更新する。

        Args:
            asset_id (int): 備品ID。
            status (str): 更新後状態。
            version_no (int): 更新前version。

        Returns:
            bool: 更新成功時True。

        要件ID: RQ-FT-REGISTER-LOAN
        設計ID: DS-FN-ASSET-OPTIMISTIC-LOCK-FT-REGISTER-LOAN
        要件概要: 貸出/返却時の同時更新競合を防ぐこと。
        設計概要: version_no一致時のみ更新し、競合時は失敗として扱う。
        呼び出し先設計ID: DS-SC-ASSETS-DT-ASSET-ENTITY
        呼び出し元設計ID: DS-CL-LOAN-SERVICE-FT-REGISTER-LOAN
        """
        cur = self.conn.execute(
            """
            UPDATE assets
            SET status = ?, version_no = version_no + 1
            WHERE asset_id = ? AND version_no = ?
            """,
            (status, asset_id, version_no),
        )
        return cur.rowcount == 1
