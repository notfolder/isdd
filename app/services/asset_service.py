"""
備品サービスモジュール。

要件ID: RQ-FT-MANAGE-ASSET-MASTER
設計ID: DS-CL-ASSET-SERVICE-FT-MANAGE-ASSET-MASTER
要件概要: 備品マスタ管理と一覧表示を提供する。
設計概要: リポジトリを通じて備品登録・更新・一覧検索を実行する。
呼び出し先設計ID: DS-CL-ASSET-REPOSITORY-DT-ASSET-ENTITY, DS-FN-MANAGE-ASSET-MASTER-FT-MANAGE-ASSET-MASTER, DS-FN-VIEW-ASSET-STATUS-FT-VIEW-ASSET-STATUS
呼び出し元設計ID: DS-IF-ASSET-LIST-SCREEN-UI-ASSET-LIST-SCREEN
"""

from __future__ import annotations

from app.models.entities import Asset, AssetStatusView
from app.repositories.asset_repository import AssetRepository


class AssetService:
    """
    備品管理処理を提供するサービスクラス。

    要件ID: RQ-FT-MANAGE-ASSET-MASTER
    設計ID: DS-CL-ASSET-SERVICE-FT-MANAGE-ASSET-MASTER
    要件概要: 管理担当者が備品情報を管理できること。
    設計概要: 備品リポジトリを使って一覧取得と更新を行う。
    呼び出し先設計ID: DS-CL-ASSET-REPOSITORY-DT-ASSET-ENTITY
    呼び出し元設計ID: DS-IF-ASSET-LIST-SCREEN-UI-ASSET-LIST-SCREEN
    """

    def __init__(self, asset_repository: AssetRepository) -> None:
        """
        AssetServiceを初期化する。

        Args:
            asset_repository (AssetRepository): 備品リポジトリ。

        要件ID: RQ-FT-MANAGE-ASSET-MASTER
        設計ID: DS-CL-ASSET-SERVICE-FT-MANAGE-ASSET-MASTER
        要件概要: 備品管理処理を一貫して実行できること。
        設計概要: リポジトリ依存を注入する。
        呼び出し先設計ID: なし
        呼び出し元設計ID: DS-MD-STREAMLIT-UI-UI-ASSET-LIST-SCREEN
        """
        self.asset_repository = asset_repository

    def list_assets_with_status(self, keyword: str) -> list[AssetStatusView]:
        """
        備品一覧を取得する。

        Args:
            keyword (str): 検索キーワード。

        Returns:
            list[AssetStatusView]: 一覧表示データ。

        要件ID: RQ-FT-VIEW-ASSET-STATUS
        設計ID: DS-FN-VIEW-ASSET-STATUS-FT-VIEW-ASSET-STATUS
        要件概要: 備品状態と貸出中利用者を一覧で確認できること。
        設計概要: リポジトリの結合検索を利用して表示データを返す。
        呼び出し先設計ID: DS-CL-ASSET-REPOSITORY-DT-ASSET-ENTITY
        呼び出し元設計ID: DS-IF-ASSET-LIST-SCREEN-UI-ASSET-LIST-SCREEN
        """
        return self.asset_repository.list_assets_with_status(keyword)

    def save_asset_master(self, asset_code: str, asset_name: str, location: str) -> None:
        """
        備品マスタを登録する。

        Args:
            asset_code (str): 備品管理番号。
            asset_name (str): 備品名。
            location (str): 保管場所。

        要件ID: RQ-FT-MANAGE-ASSET-MASTER
        設計ID: DS-FN-MANAGE-ASSET-MASTER-FT-MANAGE-ASSET-MASTER
        要件概要: 備品の新規登録と更新ができること。
        設計概要: 新規備品としてstatus=availableで保存する。
        呼び出し先設計ID: DS-CL-ASSET-REPOSITORY-DT-ASSET-ENTITY
        呼び出し元設計ID: DS-IF-ASSET-LIST-SCREEN-UI-ASSET-LIST-SCREEN
        """
        self.asset_repository.save_asset(
            Asset(
                asset_id=0,
                asset_code=asset_code,
                asset_name=asset_name,
                location=location,
                status="available",
                version_no=1,
            )
        )
