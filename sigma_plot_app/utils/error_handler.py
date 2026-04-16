"""
エラーハンドリングユーティリティ - エラー検出・処理機能

- データ検証
- エラーメッセージの生成
"""

from typing import List, Dict, Any


class ValidationError(Exception):
    """データ検証エラー"""

    pass


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


def check_file_size(file_path: str) -> tuple:
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


def validate_data(data_1: List[Any], data_2: List[Any]) -> str:
    """データを検証

    Args:
        data_1: 第 1 データのリスト
        data_2: 第 2 データのリスト

    Returns:
        エラーメッセージ（エラーがない場合は空文字列）
    """
    errors = []

    # 数値データの検証
    if not validate_numeric_data(data_1):
        errors.append("カラム 1 は数値データではありません")

    if not validate_numeric_data(data_2):
        errors.append("カラム 2 は数値データではありません")

    # データ長の検証
    if len(data_1) != len(data_2):
        errors.append(
            f"データの長さが一致しません（カラム 1: {len(data_1)}, カラム 2: {len(data_2)})"
        )

    # データ行数の制限
    if len(data_1) > 10000:
        errors.append(f"データ行数が多すぎます（{len(data_1)} 行）")

    return "; ".join(errors) if errors else ""


def handle_error(error_type: str, message: str) -> None:
    """エラーを処理

    Args:
        error_type: エラータイプ（"file", "column", "data", "plot"）
        message: エラーメッセージ

    Raises:
        Exception: 指定されたエラータイプに応じて例外をスロー
    """
    if error_type == "file":
        raise FileNotFoundError(message)

    elif error_type == "column":
        if "Not a CSV file" in message:
            raise ValueError("CSV ファイルを選択してください")
        elif "Too many columns" in message:
            raise ValueError("選択可能なカラムが 2 つ未満です")
        elif "Non-numeric data" in message:
            raise ValueError("数値カラムを選択してください")
        else:
            raise ValueError(message)

    elif error_type == "data":
        if "Data length mismatch" in message:
            raise ValueError("データの長さが一致しません")
        else:
            raise ValueError(message)

    elif error_type == "plot":
        # プロットエラーはログ出力で処理
        print(f"Plot error: {message}")
