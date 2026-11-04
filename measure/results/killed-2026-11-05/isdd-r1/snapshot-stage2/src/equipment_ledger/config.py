"""設定の読み込み。環境変数から起動時の設定を読む。"""

import os
from pathlib import Path


def load_config(environ=None):
    """環境変数から設定を読み、辞書で返す。

    キー: port（待ち受けポート、既定 8000）、host（待ち受けアドレス、既定 0.0.0.0）、
    data_dir（DB と署名鍵の置き場所、既定 ./data）、idle_timeout_seconds（無操作の自動ログアウトまでの秒数、既定 1800）。
    """
    env = os.environ if environ is None else environ
    return {
        "port": int(env.get("PORT", "8000")),
        "host": env.get("HOST", "0.0.0.0"),
        "data_dir": Path(env.get("DATA_DIR", "./data")),
        "idle_timeout_seconds": int(env.get("SESSION_IDLE_TIMEOUT_SECONDS", "1800")),
    }
