"""モニターの貸出。物の登録、貸出、返却、履歴を扱う。"""

from flask import Blueprint

from app.modules.monitors.queries import SCHEMA

TITLE = "モニターの貸出"

bp = Blueprint("monitors", __name__, url_prefix="/monitors", template_folder="templates")

# ルートの登録（循環参照を避けるため bp の作成後に読み込む）
from app.modules.monitors import handlers  # noqa: E402,F401

__all__ = ["bp", "TITLE", "SCHEMA"]
