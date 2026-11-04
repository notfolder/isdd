"""環境変数から設定値を読む。"""

import os


def load_settings() -> dict:
    """環境変数を読んで設定の辞書（host、port、data_dir、idle_timeout_seconds）にする。未設定なら既定値を使う。"""
    return {
        "host": os.environ.get("HOST", "0.0.0.0"),
        "port": int(os.environ.get("PORT", "8000")),
        "data_dir": os.path.abspath(os.environ.get("DATA_DIR", "./data")),
        "idle_timeout_seconds": int(os.environ.get("SESSION_IDLE_TIMEOUT_SECONDS", "1800")),
    }
