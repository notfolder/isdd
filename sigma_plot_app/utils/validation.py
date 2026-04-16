"""
検証ユーティリティ - データ検証機能

- 数値データの検証
- ファイルサイズのチェック
"""

import os
from typing import List, Any


def validate_numeric_data(data: List[Any]) -> bool:
    """数値データを検証

    Args:
        data: 検証対象のデータリスト

    Returns:
        数値データの場合は True、そうでない場合は False
    """
    if not data:
        return False

    # 空のリストは数値データとして扱う
    if len(data) == 0:
        return True

    # 最初の要素が数値か確認
    try:
        float(data[0])
        return True
    except (ValueError, TypeError):
        return False


def check_file_size(file_path: str) -> Tuple[bool, int]:
    """ファイルサイズを確認

    Args:
        file_path: ファイルパス

    Returns:
        (サイズ制限内か、ファイルサイズ)
    """
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    if not os.path.exists(file_path):
        return False, 0

    file_size = os.path.getsize(file_path)
    is_within_limit = file_size <= MAX_FILE_SIZE

    return is_within_limit, file_size


def validate_column_names(column_names: List[str]) -> bool:
    """カラム名の検証

    Args:
        column_names: カラム名のリスト

    Returns:
        検証に成功した場合は True、失敗した場合は False
    """
    if len(column_names) != 2:
        return False

    for name in column_names:
        if not name or len(name) == 0:
            return False

    return True


def validate_data_length(data_1: List[Any], data_2: List[Any]) -> bool:
    """データ長の検証

    Args:
        data_1: 第 1 データのリスト
        data_2: 第 2 データのリスト

    Returns:
        データ長が一致している場合は True、そうでない場合は False
    """
    if len(data_1) != len(data_2):
        return False

    # データ行数の制限（10,000 行）
    if len(data_1) > 10000:
        return False

    return True
