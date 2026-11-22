"""トップ。機能の一覧。"""

from flask import Blueprint, current_app, render_template

from app.core.auth import login_required

bp = Blueprint("home", __name__)


@bp.route("/")
@login_required
def index():
    return render_template("home.html", modules=current_app.config["MODULES"])
