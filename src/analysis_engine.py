import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
# 共通正規化処理は utils/utils.py などに定義されていると仮定


class AnalysisEngine:
    """
    データセットに対して統計的な計算や分析を実行するエンジン。
    Q-Qプロット生成や記述統計量の算出を行う。
    """

    def __init__(self, logger_manager):
        # ログマネージャーを依存性注入 (DI) で受け取ることで、ロギングの一貫性を保つ
        self.logger = logger_manager

    def calculate_descriptive_stats(self, df: pd.DataFrame, column_name: str) -> dict:
        """
        指定されたカラムの基本的な記述統計量（平均、標準偏差など）を計算する。

        Args:
            df (pd.DataFrame): データフレーム。
            column_name (str): 分析対象のカラム名。

        Returns:
            dict: 統計量の辞書。
        """
        if column_name not in df.columns:
            raise ValueError(f"カラム '{column_name}' はデータセットに見つかりません。")

        data = df[column_name].dropna()  # NaNを除外して計算

        stats_result = {
            "count": len(data),
            "mean": data.mean(),
            "std": data.std(),
            "median": data.median(),
            "min": data.min(),
            "max": data.max(),
        }
        self.logger.log_event(
            "ANALYZE_SUCCESS",
            f"{column_name} の記述統計量を計算しました。",
            "基礎的な統計指標が算出されました。",
        )
        return stats_result

    def calculate_qqplot(self, data: np.ndarray) -> plt.Figure:
        """
        データのQ-Qプロットを生成する（正規性の簡易チェック）。

        Args:
            data (np.ndarray): 分析対象の一次元データ配列。

        Returns:
            plt.Figure: 生成されたmatplotlib Figureオブジェクト。
        """
        if data is None or len(data) < 2:
            raise ValueError(
                "Q-Qプロットを生成するには、少なくとも2つのデータポイントが必要です。"
            )

        # scipyのstats.probplotを使用するのが標準的
        stat_result = stats.probplot(data, dist="norm", plot=plt)

        self.logger.log_event(
            "ANALYZE_START",
            "Q-Qプロット生成を開始しました。",
            "データの正規性チェックを実行しました。",
        )
        return stat_result.fig
