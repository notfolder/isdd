import pandas as pd
from typing import List, Optional


class DataHandler:
    """
    Service for file I/O and dataframe operations.
    Handles loading CSV files, validation of numeric columns,
    and extraction of metadata like column names.
    """

    def __init__(self):
        pass

    def load_csv(self, file) -> pd.DataFrame:
        """
        Loads a CSV file into a Pandas DataFrame.

        Args:
            file: The uploaded file object (compatible with Streamlit/BytesIO).

        Returns:
            pd.DataFrame: The loaded data.

        Raises:
            ValueError: If the file is not a valid CSV or cannot be parsed.
        """
        try:
            df = pd.read_csv(file)
            return df
        except Exception as e:
            raise ValueError(f"Failed to load CSV: {e}")

    def get_column_names(self, df: pd.DataFrame) -> List[str]:
        """
        Extracts column names from a DataFrame.

        Args:
            df: The input DataFrame.

        Returns:
            List[str]: A list of column names.
        """
        if df is None or df.empty:
            return []
        return df.columns.tolist()

    def validate_numeric_columns(self, df: pd.DataFrame, columns: List[str]) -> bool:
        """
        Validates that the selected columns contain only numeric data.

        Args:
            df: The input DataFrame.
            columns: A list of column names to validate.

        Returns:
            bool: True if all specified columns are numeric, False otherwise.
        """
        if df is None or df.empty:
            return False

        for col in columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                return False
        return True
