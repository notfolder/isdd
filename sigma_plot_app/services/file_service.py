"""
ファイルサービス - CSV ファイルの読み込み・検証処理

- ファイルの存在確認
- CSV 形式の検証
- データ読み込み
"""

import os
from typing import Dict, List, Tuple


class FileService:
    """ファイル処理サービス"""

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(self):
        """初期化処理"""
        pass

    def check_file_exists(self, file_path: str) -> bool:
        """ファイルが存在するか確認

        Args:
            file_path: ファイルパス

        Returns:
            ファイルが存在する場合は True、そうでない場合は False
        """
        return os.path.exists(file_path)

    def check_file_size(self, file_path: str) -> Tuple[bool, int]:
        """ファイルサイズを確認

        Args:
            file_path: ファイルパス

        Returns:
            (サイズ制限内か、ファイルサイズ)
        """
        if not os.path.exists(file_path):
            return False, 0

        file_size = os.path.getsize(file_path)
        is_within_limit = file_size <= self.MAX_FILE_SIZE

        return is_within_limit, file_size

    def validate_csv_format(self, file_path: str) -> Tuple[bool, str]:
        """CSV 形式を検証

        Args:
            file_path: ファイルパス

        Returns:
            (CSV 形式か、エラーメッセージ)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                # ヘッダー行を確認
                header = f.readline().strip()

                if not header:
                    return False, "ファイルが空です"

                # CSV 形式の検証（カンマ区切り）
                if "," not in header and "\t" not in header:
                    return False, "CSV 形式のファイルではありません"

                # データ行を確認（数行）
                line_count = 0
                for i, line in enumerate(f):
                    if i >= 5:  # ヘッダー + 5 行まで確認
                        break
                    line_count += 1

                return True, ""

        except Exception as e:
            return False, f"ファイルの読み込みに失敗しました：{str(e)}"

    def read_csv(self, file_path: str) -> Tuple[List[str], List[List[str]]]:
        """CSV ファイルを読み込む

        Args:
            file_path: ファイルパス

        Returns:
            (ヘッダー行、データ行のリスト)
        """
        headers = []
        data_rows = []

        with open(file_path, "r", encoding="utf-8") as f:
            # ヘッダー行の読み込み
            header_line = f.readline().strip()

            # ヘッダーをパース（カンマ区切り）
            headers = [h.strip() for h in header_line.split(",")]

            # データ行の読み込み
            for line in f:
                row = [cell.strip() for cell in line.split(",")]
                data_rows.append(row)

        return headers, data_rows

    def load_csv(self, file_path: str) -> Dict[str, List[float]]:
        """CSV ファイルからカラムデータを読み込む

        Args:
            file_path: ファイルパス

        Returns:
            カラム名をキー、数値データのリストを値として持つ辞書

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            ValueError: CSV 形式でない、数値データでないなどのエラー
        """
        # ファイル存在確認
        if not self.check_file_exists(file_path):
            raise FileNotFoundError(f"ファイルが見つかりません：{file_path}")

        # ファイルサイズ確認
        is_within_limit, file_size = self.check_file_size(file_path)
        if not is_within_limit:
            raise ValueError(
                f"ファイルサイズが制限を超えています（{file_size / 1024 / 1024:.2f} MB）"
            )

        # CSV 形式検証
        is_csv, error_msg = self.validate_csv_format(file_path)
        if not is_csv:
            raise ValueError(error_msg)

        # CSV を読み込む
        headers, data_rows = self.read_csv(file_path)

        # カラム名とデータ行数を確認
        if len(headers) < 2:
            raise ValueError("選択可能なカラムが 2 つ未満です")

        # データ行数を確認
        if len(data_rows) == 0:
            raise ValueError("データが空です")

        if len(data_rows) > 10000:
            raise ValueError(f"データ行数が多すぎます（{len(data_rows)} 行）")

        # カラムデータに変換（数値型へ）
        columns_data = {}
        for header in headers:
            try:
                column_data = [float(row[i]) for row in data_rows]
                columns_data[header] = column_data
            except (ValueError, IndexError) as e:
                raise ValueError(f"カラム '{header}' は数値データではありません")

        return columns_data
