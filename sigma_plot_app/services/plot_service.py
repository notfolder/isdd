"""
プロットサービス - Q-Q プロットとヒストグラムの生成・描画

- Q-Q プロットの計算
- ヒストグラムの計算
- プロットの描画（matplotlib）
- プロットの保存
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Any, Tuple


class PlotService:
    """プロット生成サービス"""

    def __init__(self):
        """初期化処理"""
        pass

    def calculate_percentiles(self, data: list, n: int = 100) -> Tuple[list, list]:
        """百分位数を計算

        Args:
            data: データのリスト
            n: 百分位数の数（デフォルト 100）

        Returns:
            (理論百分位数、実測百分位数) のタプル
        """
        sorted_data = sorted(data)

        # 理論百分位数（標準正規分布）
        theoretical_percentiles = [
            np.percentile(np.random.randn(10000), (i + 1) * 100 / n) for i in range(n)
        ]

        # 実測百分位数
        measured_percentiles = [
            sorted_data[int(i * len(sorted_data) / n)] for i in range(n)
        ]

        return theoretical_percentiles, measured_percentiles

    def calculate_qq_plot_data(self, data_1: list, data_2: list) -> Any:
        """Q-Q プロットのデータを計算

        Args:
            data_1: 第 1 データのリスト
            data_2: 第 2 データのリスト

        Returns:
            Q-Q プロット描画用のデータ（matplotlib.axes.Axes）
        """
        # データ長を確認
        if len(data_1) != len(data_2):
            raise ValueError("データの長さが一致しません")

        # 百分位数を計算（n=100）
        n = 100
        theoretical_1, measured_1 = self.calculate_percentiles(data_1, n)
        theoretical_2, measured_2 = self.calculate_percentiles(data_2, n)

        # Q-Q プロットを描画
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        # Q-Q プロット 1（data_1 vs data_2）
        axes[0].plot(theoretical_1, measured_1, "bo", markersize=3)
        axes[0].plot(
            [min(theoretical_1), max(theoretical_1)],
            [min(measured_1), max(measured_1)],
            "r-",
        )
        axes[0].set_xlabel("Theoretical Quantiles (data_1)")
        axes[0].set_ylabel("Observed Quantiles (data_2)")
        axes[0].set_title(f"Q-Q Plot: data_1 vs data_2")
        axes[0].grid(True, alpha=0.3)

        # Q-Q プロット 2（data_2 vs data_1）
        axes[1].plot(theoretical_2, measured_2, "bo", markersize=3)
        axes[1].plot(
            [min(theoretical_2), max(theoretical_2)],
            [min(measured_2), max(measured_2)],
            "r-",
        )
        axes[1].set_xlabel("Theoretical Quantiles (data_2)")
        axes[1].set_ylabel("Observed Quantiles (data_1)")
        axes[1].set_title(f"Q-Q Plot: data_2 vs data_1")
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()

        return fig

    def calculate_histogram(self, data_1: list, data_2: list, bins: int = 50) -> Any:
        """ヒストグラムデータを計算

        Args:
            data_1: 第 1 データのリスト
            data_2: 第 2 データのリスト
            bins: バイン数（デフォルト 50）

        Returns:
            ヒストグラム描画用のデータ（matplotlib.axes.Axes）
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        # ヒストグラムを重ねて描画
        ax.hist(data_1, bins=bins, alpha=0.5, label="data_1", color="skyblue")
        ax.hist(data_2, bins=bins, alpha=0.5, label="data_2", color="salmon")

        ax.set_xlabel("Value")
        ax.set_ylabel("Frequency")
        ax.set_title("Histogram Comparison")
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        return fig

    def render_qq_plot(self, qq_plot_data: Any) -> Any:
        """Q-Q プロットを描画

        Args:
            qq_plot_data: Q-Q プロット描画用のデータ

        Returns:
            描画されたプロット（matplotlib.figure.Figure）
        """
        return qq_plot_data

    def render_qq_plot_with_histograms(self, qq_plot_data: Any, hist_data: Any) -> Any:
        """Q-Q プロットにヒストグラムを重ねて描画

        Args:
            qq_plot_data: Q-Q プロット描画用のデータ
            hist_data: ヒストグラム描画用のデータ

        Returns:
            重ね描きされたプロット（matplotlib.figure.Figure）
        """
        # Q-Q プロットの描画
        qq_fig = self.render_qq_plot(qq_plot_data)

        # ヒストグラムの描画（新しいウィンドウ）
        hist_fig = self.render_histogram(hist_data)

        return qq_fig

    def render_histogram(self, hist_data: Any) -> Any:
        """ヒストグラムを描画

        Args:
            hist_data: ヒストグラム描画用のデータ

        Returns:
            描画されたプロット（matplotlib.figure.Figure）
        """
        return hist_data

    def save_plot(self, plot: Any, filepath: str) -> bool:
        """プロットを保存

        Args:
            plot: 描画されたプロット（matplotlib.figure.Figure）
            filepath: 保存パス

        Returns:
            保存に成功した場合は True、失敗した場合は False
        """
        try:
            plot.savefig(filepath, dpi=150, bbox_inches="tight")
            return True
        except Exception as e:
            print(f"保存に失敗しました：{e}")
            return False
