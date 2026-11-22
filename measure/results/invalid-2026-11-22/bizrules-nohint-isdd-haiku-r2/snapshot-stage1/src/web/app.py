"""Flask アプリを組み立てる。業務層のサービスは引数で受け取り、ここでは作らない。"""

from flask import Flask, render_template

from service.errors import NotFoundError
from service.permissions import PermissionDenied
from web.auth import current_user
from web.views import register_routes


def create_app(services, secret_key: str) -> Flask:
    """画面のアプリを作る。

    引数 services: accounts・equipment・lending を持つ業務層の入れ物。
    引数 secret_key: セッションの署名に使う秘密の値。
    戻り値: 設定済みの Flask アプリ。
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.update(
        SECRET_KEY=secret_key,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        MAX_CONTENT_LENGTH=64 * 1024,
    )
    app.extensions["services"] = services
    app.context_processor(_inject_user)
    app.register_error_handler(PermissionDenied, handle_permission_denied)
    app.register_error_handler(NotFoundError, handle_not_found)
    register_routes(app)
    return app


def _inject_user() -> dict:
    """全画面に、ログイン中の利用者（無ければ None）を渡す。"""
    return {"user": current_user()}


def handle_permission_denied(error: PermissionDenied):
    """権限が無い操作を 403 の画面で返す。文言は `.error` に出す。"""
    return render_template("error.html", error=str(error)), 403


def handle_not_found(error: NotFoundError):
    """存在しない備品や利用者を 404 の画面で返す。"""
    return render_template("error.html", error="対象が見つかりません"), 404
