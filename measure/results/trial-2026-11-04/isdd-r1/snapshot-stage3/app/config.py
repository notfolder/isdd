"""環境変数の読み取りと、秘密鍵（フラッシュメッセージ用の署名）の準備。"""

import os
import secrets
from dataclasses import dataclass

DEFAULT_PORT = 8000
DEFAULT_DATA_DIR = "data"
DEFAULT_IDLE_TIMEOUT_SECONDS = 1800
SECRET_KEY_FILE = "secret_key"


@dataclass(frozen=True)
class _Settings:
    """起動時に決まる設定値。"""

    port: int
    data_dir: str
    idle_timeout_seconds: int


def load_config(environ=None) -> _Settings:
    """環境変数から設定を読む。未指定なら既定値を使う。

    引数 environ は環境変数の辞書（省略時は os.environ）。
    """
    env = os.environ if environ is None else environ
    port = int(env.get("PORT") or DEFAULT_PORT)
    data_dir = env.get("DATA_DIR") or DEFAULT_DATA_DIR
    idle = int(env.get("SESSION_IDLE_TIMEOUT_SECONDS") or DEFAULT_IDLE_TIMEOUT_SECONDS)
    return _Settings(port=port, data_dir=data_dir, idle_timeout_seconds=idle)


def load_or_create_secret_key(data_dir: str) -> str:
    """DATA_DIR の秘密鍵を返す。無ければ生成して保存する（権限は所有者だけ）。"""
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, SECRET_KEY_FILE)
    try:
        with open(path, "r", encoding="utf-8") as f:
            key = f.read().strip()
        if key:
            return key
    except FileNotFoundError:
        pass
    key = secrets.token_hex(32)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(key)
    return key
