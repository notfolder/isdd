"""環境変数から設定を読む。"""

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PORT = 8000
DEFAULT_DATA_DIR = "./data"
DEFAULT_IDLE_TIMEOUT_SECONDS = 1800
DB_FILE_NAME = "isdd.sqlite3"


@dataclass(frozen=True)
class _Settings:
    """起動時に読んだ設定の値。"""

    port: int
    data_dir: Path
    idle_timeout_seconds: int

    @property
    def db_path(self) -> Path:
        """DB ファイルの場所（DATA_DIR の直下）。"""
        return self.data_dir / DB_FILE_NAME


def _read_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if raw == "":
        return default
    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError(f"{name} は整数で指定してください: {raw!r}") from error
    if value <= 0:
        raise ValueError(f"{name} は 1 以上の整数で指定してください: {raw!r}")
    return value


def load_settings() -> _Settings:
    """環境変数 PORT、DATA_DIR、SESSION_IDLE_TIMEOUT_SECONDS を読む。

    無ければ既定値を使う（PORT は 8000、DATA_DIR は ./data、タイムアウトは 1800 秒）。

    Returns:
        読み込んだ設定。
    """
    port = _read_int("PORT", DEFAULT_PORT)
    data_dir = Path(os.environ.get("DATA_DIR", "").strip() or DEFAULT_DATA_DIR)
    timeout = _read_int("SESSION_IDLE_TIMEOUT_SECONDS", DEFAULT_IDLE_TIMEOUT_SECONDS)
    return _Settings(port=port, data_dir=data_dir, idle_timeout_seconds=timeout)
