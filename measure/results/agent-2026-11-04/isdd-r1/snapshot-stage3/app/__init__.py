"""備品台帳アプリの生成。"""

import os
import secrets
from pathlib import Path
from typing import Dict, Optional

from flask import Flask

from .config import load_config
from .db import DB_FILE_NAME, init_schema
from .views import web_blueprint

SECRET_KEY_FILE_NAME = "secret_key"


def load_or_create_secret_key(data_dir: Path) -> str:
    """秘密鍵を読む。無ければ乱数で作り、権限 0600 で保存する。"""
    path = data_dir / SECRET_KEY_FILE_NAME
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    key = secrets.token_hex(32)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(key)
    return key


def create_app(config: Optional[Dict[str, object]] = None) -> Flask:
    """設定に従ってアプリを作る。DB と秘密鍵を準備し、画面を登録する。"""
    if config is None:
        config = load_config()
    data_dir = Path(config["data_dir"])
    data_dir.mkdir(parents=True, exist_ok=True)
    app = Flask(__name__)
    db_path = data_dir / DB_FILE_NAME
    app.config.update(
        SECRET_KEY=load_or_create_secret_key(data_dir),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        IDLE_TIMEOUT_SECONDS=int(config["idle_timeout_seconds"]),
        DB_PATH=str(db_path),
    )
    init_schema(db_path)
    app.register_blueprint(web_blueprint)
    return app
