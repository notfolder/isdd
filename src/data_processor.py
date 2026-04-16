import pandas as pd
from typing import List, Tuple, Optional
from utils.validators import check_is_numeric  # 仮定した共通バリデータを使用


class DataProcessor:
    """
    CSVファイルの読み込み、データ型バリデーションを行い、Pandas DataFrameとしてデータを保持する。
    """

    def __init__(self):
        pass

    def load_data(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        指定されたパスからCSVファイルを読み込み、初期のデータバリデーションを行う。

        Args:
            file_path (str): CSVファイルの絶対パスまたは相対パス。

        Returns:
            Optional[pd.DataFrame]: 読み込まれたデータフレーム。エラー時はNoneを返す。
        """
        try:
            # CSVファイルをPandasで読み込む
            df = pd.read_csv(file_path)
            print(f"Successfully loaded data from {file_path}. Shape: {df.shape}")
            return df
        except FileNotFoundError:
            raise ValueError(
                f"FileNotFoundError: 指定されたファイルパス '{file_path}' が見つかりません。"
            )
        except pd.errors.EmptyDataError:
            raise ValueError("EmptyDataError: ファイルが空です。")
        except Exception as e:
            raise Exception(f"Unknown error during data loading: {e}")

    def validate_columns(
        self, df: pd.DataFrame, columns_to_check: List[str]
    ) -> Tuple[Optional[pd.DataFrame], List[str]]:
        """
        指定されたカラムが全て数値型であり、かつデータセットとして有効であることを検証する。

        Args:
            df (pd.DataFrame): 検証対象のデータフレーム。
            columns_to_check (List[str]): 数値検証を行うカラム名のリスト。

        Returns:
            Tuple[Optional[pd.DataFrame], List[str]]: 処理可能なデータフレームと、検証エラーが発生したカラム名（空の場合は[]）。
        """
        valid_cols = []
        error_cols = []
        df_to_process = df.copy()

        for col in columns_to_check:
            if col not in df.columns:
                print(f"Warning: カラム '{col}' はデータセットに含まれていません。")
                error_cols.append(col)
                continue

            # 共通バリデーション（ここでは簡略化し、Pandasのdtypesを使用）
            if check_is_numeric(df[col]):
                valid_cols.append(col)
            else:
                print(
                    f"Validation Failed: カラム '{col}' は数値データとして不適切です。"
                )
                error_cols.append(col)

        if not valid_cols:
            raise ValueError(
                "すべての指定されたカラムが検証に失敗したため、処理を続行できませんでした。"
            )

        # 検証を通過したカラムのみを持つデータフレームを返す（これがコアのロジック）
        df_validated = df[valid_cols]
        return df_validated, error_cols
