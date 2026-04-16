# utils/validators.py の内容を想定し、ファイルが存在しないためダミーで作成します
def check_is_numeric(series: pd.Series) -> bool:
    """
    シリーズが数値データ（float, int）のみで構成されているかチェックする。
    """
    # NaN値は許容することが多いが、ここでは厳密に数値型をチェックする
    return pd.to_numeric(series, errors="coerce").notna().all()
