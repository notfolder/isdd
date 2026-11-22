"""工具の貸出。物の登録と、社員への貸出・返却を扱う。"""

from flask import Blueprint

from app.modules.tools.queries import SCHEMA

TITLE = "工具の貸出"

bp = Blueprint("tools", __name__, url_prefix="/tools", template_folder="templates")

from app.modules.tools import handlers  # noqa: E402,F401  ルートの登録
