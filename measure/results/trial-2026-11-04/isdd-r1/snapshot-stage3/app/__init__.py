"""備品台帳アプリの組み立て。起動時に設定を読み、秘密鍵と表を準備する。"""

import os

from flask import Flask

from . import auth, config, db, views


def create_app() -> Flask:
    """Flask アプリを作る。DATA_DIR が無ければ作り、表が無ければ作る。"""
    cfg = config.load_config()
    app = Flask(__name__)
    app.config["DATA_DIR"] = cfg.data_dir
    app.config["SECRET_KEY"] = config.load_or_create_secret_key(cfg.data_dir)
    app.config["SESSION_IDLE_TIMEOUT_SECONDS"] = cfg.idle_timeout_seconds
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    os.makedirs(cfg.data_dir, exist_ok=True)
    conn = db.connect(cfg.data_dir)
    try:
        db.init_schema(conn)
    finally:
        conn.close()
    app.register_blueprint(views.bp)
    return app
