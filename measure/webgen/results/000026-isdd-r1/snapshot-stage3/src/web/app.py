"""Flask の画面: ルーティング、入力の検証、描画。投票者（ブラウザ）の判定を含む。"""

import re
import uuid
from typing import Optional

from flask import (
    Flask,
    abort,
    current_app,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)

from store.db import cast_vote, get_poll, has_voted, list_polls

VOTE_ERROR = "Please select one option before you vote."
ALREADY_VOTED = "You have already voted"

VOTER_COOKIE = "voter_id"
VOTER_COOKIE_MAX_AGE = 365 * 24 * 60 * 60  # 1 年（秒）
VOTER_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")

# 画面の endpoint と、ナビゲーションで強調する項目の対応
NAV_SECTION = {
    "show_poll_list": "Surveys",
    "show_poll_detail": "Surveys",
    "submit_vote": "Surveys",
    "show_poll_results": "Results",
    "show_results_overview": "Results",
}


def create_app(db_path: str) -> Flask:
    """Flask アプリを作り、画面のルートとエラー処理とナビゲーションを登録する。"""
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path
    app.add_url_rule("/", "show_poll_list", show_poll_list)
    app.add_url_rule("/surveys/<int:poll_id>", "show_poll_detail", show_poll_detail)
    app.add_url_rule(
        "/surveys/<int:poll_id>/vote", "submit_vote", submit_vote, methods=["POST"]
    )
    app.add_url_rule(
        "/surveys/<int:poll_id>/results", "show_poll_results", show_poll_results
    )
    app.add_url_rule("/results", "show_results_overview", show_results_overview)
    app.register_error_handler(404, handle_not_found)
    app.context_processor(provide_navigation)
    return app


def provide_navigation():
    """全画面のナビゲーション項目と、現在の画面の項目を返す。"""
    current = NAV_SECTION.get(request.endpoint)
    items = [
        {"label": "Surveys", "endpoint": "show_poll_list"},
        {"label": "Results", "endpoint": "show_results_overview"},
    ]
    for item in items:
        item["active"] = item["label"] == current
    return {"nav_items": items}


def read_voter_cookie() -> Optional[str]:
    """リクエストの Cookie から投票者 ID を読む。無い、または形式が違うときは None。"""
    value = request.cookies.get(VOTER_COOKIE, "")
    return value if VOTER_ID_PATTERN.match(value) else None


def set_voter_cookie(response, voter_id: str):
    """応答に投票者 ID の Cookie を付けて返す（HttpOnly、SameSite=Lax、1 年）。"""
    response.set_cookie(
        VOTER_COOKIE,
        voter_id,
        max_age=VOTER_COOKIE_MAX_AGE,
        path="/",
        httponly=True,
        samesite="Lax",
    )
    return response


def _detail_page(poll, status: int, error=None, already_voted: bool = False):
    """投票の詳細画面を指定の状態コードで作る。投票者 ID の Cookie は呼び出し側で付ける。"""
    html = render_template(
        "poll_detail.html", poll=poll, error=error, already_voted=already_voted
    )
    return make_response(html, status)


def show_poll_list():
    """投票テーマの一覧画面を返す。"""
    polls = list_polls(current_app.config["DB_PATH"])
    return render_template("poll_list.html", polls=polls)


def show_poll_detail(poll_id: int):
    """投票テーマの質問と選択肢、投票のフォームを返す。投票済みのブラウザには投票の操作を無効にする。無ければ 404。"""
    db_path = current_app.config["DB_PATH"]
    poll = get_poll(db_path, poll_id)
    if poll is None:
        abort(404)
    voter_id = read_voter_cookie()
    already = voter_id is not None and has_voted(db_path, poll_id, voter_id)
    return render_template(
        "poll_detail.html", poll=poll, error=None, already_voted=already
    )


def submit_vote(poll_id: int):
    """選んだ選択肢に 1 票を記録し、結果画面へ移る。投票済みのブラウザは記録せず 409 で知らせる。不正な入力は詳細画面に戻して知らせる。"""
    db_path = current_app.config["DB_PATH"]
    poll = get_poll(db_path, poll_id)
    if poll is None:
        abort(404)
    voter_id = read_voter_cookie() or uuid.uuid4().hex
    if has_voted(db_path, poll_id, voter_id):
        return set_voter_cookie(_detail_page(poll, 409, already_voted=True), voter_id)
    try:
        option_id = int(request.form.get("option_id", ""))
    except ValueError:
        return set_voter_cookie(_detail_page(poll, 400, error=VOTE_ERROR), voter_id)
    try:
        recorded = cast_vote(db_path, poll_id, option_id, voter_id)
    except ValueError:
        return set_voter_cookie(_detail_page(poll, 400, error=VOTE_ERROR), voter_id)
    if not recorded:
        # 同時に 2 回送られた場合など、保存処理の段階で投票済みと分かったとき
        return set_voter_cookie(_detail_page(poll, 409, already_voted=True), voter_id)
    response = redirect(url_for("show_poll_results", poll_id=poll_id, voted=1), code=303)
    return set_voter_cookie(response, voter_id)


def show_poll_results(poll_id: int):
    """1 つの投票テーマの票数と割合を返す。無ければ 404。"""
    poll = get_poll(current_app.config["DB_PATH"], poll_id)
    if poll is None:
        abort(404)
    voted = request.args.get("voted") == "1"
    return render_template("poll_results.html", poll=poll, voted=voted)


def show_results_overview():
    """全投票テーマの結果の一覧を返す。"""
    polls = list_polls(current_app.config["DB_PATH"])
    return render_template("results_overview.html", polls=polls)


def handle_not_found(error):
    """存在しない URL・投票テーマに対する「Not found」画面を返す。"""
    return render_template("not_found.html"), 404
