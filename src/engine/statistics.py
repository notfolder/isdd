import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any


class StatisticsEngine:
    """
    Logic for statistical calculations.
    Handles histogram binning, frequency aggregation,
    and data preparation for comparison plots (e.g., Q-Q plots).
    """

    def __init__(self):
        pass

    def calculate_histogram(
        self, df: pd.DataFrame, column: str, bins: int = 10
    ) -> Dict[str, Any]:
        """
        Calculates histogram data (bin edges and counts).

        Args:
            df: The input DataFrame.
            column: Column name to use for histogram.
            bins: Number of bins (default 10).

        Returns:
            Dict containing 'bin_edges' and 'counts'.
        """
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame.")

        data = df[column].dropna()
        if data.empty:
            return {"bin_edges": [], "counts": []}

        counts, bin_edges = np.histogram(data, bins=bins)

        return {"counts": counts.tolist(), "bin_edges": bin_edges.tolist()}

    def calculate_qq_plot_data(
        self, df: pd.DataFrame, col_a: str, col_b: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepares data for a two-sample Q-Q plot (comparing quantiles of A vs B).
        Note: For a standard two-sample Q-Q plot, samples are often sorted and paired.

        Args:
            df: The input DataFrame containing both columns.
            col_a: Column name for sample A.
            col_b: Column name for sample B.

        Returns:
            Tuple of (sorted_sample_a, sorted_sample_b) for plotting.
        """
        if col_a not in df.columns or col_b not in df.columns:
            raise ValueError("One of the specified columns is missing from DataFrame.")

        # Extract non-null values and sort them to align quantiles for comparison
        data_a = np.sort(df[col_a].dropna().values)
        data_b = np.sort(df[col_b].dropna().values)

        # For comparison plots, we often need to handle different sample sizes.
        # In a simple implementation for visualization purposes:
        min_len = min(len(data_a), len(data_b))
        return data_a[:min_len], data_b[:min_len]
