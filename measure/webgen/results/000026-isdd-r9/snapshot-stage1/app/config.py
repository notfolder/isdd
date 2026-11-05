"""Read runtime settings from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_PORT = 8000
DEFAULT_DATA_DIR = "./data"


def load_port() -> int:
    """Return the TCP port from PORT, or the default when PORT is unset."""
    raw = os.environ.get("PORT", "").strip()
    return int(raw) if raw else DEFAULT_PORT


def load_data_dir() -> Path:
    """Return DATA_DIR as a path, creating the directory when it is missing."""
    raw = os.environ.get("DATA_DIR", "").strip() or DEFAULT_DATA_DIR
    path = Path(raw).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path
