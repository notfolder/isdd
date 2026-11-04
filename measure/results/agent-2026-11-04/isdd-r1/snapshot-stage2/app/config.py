"""環境変数から設定値を読む。"""

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Dict, Optional

DEFAULT_PORT = 8000
DEFAULT_IDLE_TIMEOUT_SECONDS = 1800
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _parse_positive_int(raw: Optional[str], default: int, name: str) -> int:
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw.strip())
    except ValueError as exc:
        raise ValueError(f"{name} は正の整数で指定してください: {raw!r}") from exc
    if value <= 0:
        raise ValueError(f"{name} は正の整数で指定してください: {raw!r}")
    return value


def load_config(env: Optional[Mapping[str, str]] = None) -> Dict[str, object]:
    """環境変数（省略時は os.environ）から設定値を辞書で返す。不正な値は ValueError にする。"""
    source = os.environ if env is None else env
    port = _parse_positive_int(source.get("PORT"), DEFAULT_PORT, "PORT")
    raw_dir = source.get("DATA_DIR")
    data_dir = Path(raw_dir).expanduser() if raw_dir and raw_dir.strip() else PROJECT_ROOT / "data"
    idle = _parse_positive_int(
        source.get("SESSION_IDLE_TIMEOUT_SECONDS"),
        DEFAULT_IDLE_TIMEOUT_SECONDS,
        "SESSION_IDLE_TIMEOUT_SECONDS",
    )
    return {"port": port, "data_dir": data_dir.resolve(), "idle_timeout_seconds": idle}
