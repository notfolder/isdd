"""環境変数から起動時の設定を読む。"""

import os
from pathlib import Path

DEFAULT_PORT = 8000
DEFAULT_DATA_DIR = "data"
DEFAULT_SESSION_IDLE_TIMEOUT_SECONDS = 1800


def load_settings(env=None):
    """環境変数から設定を読み、辞書で返す。

    引数 env は環境変数の辞書（省略時は os.environ）。
    戻り値は port（整数）、data_dir（Path）、session_idle_timeout_seconds（整数）を持つ辞書。
    """
    source = os.environ if env is None else env
    return {
        "port": int(source.get("PORT", DEFAULT_PORT)),
        "data_dir": Path(source.get("DATA_DIR", DEFAULT_DATA_DIR)),
        "session_idle_timeout_seconds": int(
            source.get("SESSION_IDLE_TIMEOUT_SECONDS", DEFAULT_SESSION_IDLE_TIMEOUT_SECONDS)
        ),
    }
