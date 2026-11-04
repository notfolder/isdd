"""備品台帳アプリの作成と設定。"""

import os

from flask import Flask

from . import db

DEFAULT_PORT = 8000
DEFAULT_IDLE_TIMEOUT_SECONDS = 1800
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_settings(environ=None):
    """環境変数から設定を読む。未指定の値は既定値にする。

    引数: environ（省略時は os.environ）。
    戻り値: PORT・DATA_DIR・SESSION_IDLE_TIMEOUT_SECONDS を持つ辞書。
    """
    env = os.environ if environ is None else environ
    return {
        "PORT": int(env.get("PORT") or DEFAULT_PORT),
        "DATA_DIR": env.get("DATA_DIR") or os.path.join(PROJECT_ROOT, "data"),
        "SESSION_IDLE_TIMEOUT_SECONDS": int(
            env.get("SESSION_IDLE_TIMEOUT_SECONDS") or DEFAULT_IDLE_TIMEOUT_SECONDS
        ),
    }


def create_app(settings=None):
    """設定から Flask アプリを作る。DB と秘密鍵を初期化し、画面の入口と期限の確認を登録する。

    引数: settings（load_settings の戻り値。省略時は環境変数から読む）。
    戻り値: Flask アプリ。
    """
    from .auth import check_idle_timeout
    from .views import bp

    settings = settings or load_settings()
    app = Flask(__name__)
    os.makedirs(settings["DATA_DIR"], exist_ok=True)
    app.config["DATA_DIR"] = settings["DATA_DIR"]
    app.config["DB_PATH"] = os.path.join(settings["DATA_DIR"], "app.db")
    app.config["SESSION_IDLE_TIMEOUT_SECONDS"] = settings["SESSION_IDLE_TIMEOUT_SECONDS"]
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    db.init_db(app)
    app.teardown_appcontext(db.close_db)
    app.before_request(check_idle_timeout)
    app.register_blueprint(bp)
    return app
