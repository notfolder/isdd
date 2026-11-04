"""Flask アプリの作成。設定の反映、秘密鍵、DB の初期化、要求の前処理、画面の登録を行う。"""

import os
import secrets
import time

from flask import Flask, g

from . import views
from .auth import check_idle_timeout
from .core.db import initialize_schema, open_connection

SECRET_KEY_FILE = "secret_key"


def _load_or_create_secret_key(data_dir: str) -> str:
    """秘密鍵を DATA_DIR から読む。無ければ乱数で作り、所有者だけが読めるように保存する。"""
    path = os.path.join(data_dir, SECRET_KEY_FILE)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(key)
    return key


def create_app(settings: dict) -> Flask:
    """設定を反映した Flask アプリを作る。"""
    app = Flask(__name__)
    os.makedirs(settings["data_dir"], exist_ok=True)
    app.config["SECRET_KEY"] = _load_or_create_secret_key(settings["data_dir"])
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["DATA_DIR"] = settings["data_dir"]
    app.config["IDLE_TIMEOUT_SECONDS"] = settings["idle_timeout_seconds"]

    conn = open_connection(settings["data_dir"])
    try:
        initialize_schema(conn)
    finally:
        conn.close()

    @app.before_request
    def _idle_check() -> None:
        check_idle_timeout(app.config["IDLE_TIMEOUT_SECONDS"], time.time())

    @app.teardown_appcontext
    def _close_db(_exc: BaseException | None) -> None:
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()

    app.register_blueprint(views.bp)
    return app
