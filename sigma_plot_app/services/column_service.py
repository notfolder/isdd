"""
カラムサービス - カラムの管理機能

- カラム一覧の表示
- カラム選択処理
"""

from typing import Dict, List


class ColumnService:
    """カラム管理サービス"""

    def __init__(self):
        """初期化処理"""
        pass

    def get_columns(self, columns_data: Dict[str, List[float]]) -> List[tuple]:
        """カラム一覧を取得

        Args:
            columns_data: カラム名をキー、数値データのリストを値として持つ辞書

        Returns:
            カラム名のタプル一覧（選択用）
        """
        return list(columns_data.keys())

    def select_columns(
        self, columns_data: Dict[str, List[float]], selected_column_names: List[str]
    ) -> tuple:
        """カラムを選択

        Args:
            columns_data: カラム名をキー、数値データのリストを値として持つ辞書
            selected_column_names: 選択されたカラム名のリスト

        Returns:
            (data_1, data_2) のタプル
        """
        if len(selected_column_names) != 2:
            raise ValueError("2 つのカラムを選択してください")

        data_1 = columns_data[selected_column_names[0]]
        data_2 = columns_data[selected_column_names[1]]

        return data_1, data_2
