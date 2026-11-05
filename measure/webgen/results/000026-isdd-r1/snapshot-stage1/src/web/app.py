"""Flask の画面: ルーティング、入力の検証、描画。"""

from flask import Flask, abort, current_app, redirect, render_template, request, url_for

from store.db import cast_vote, get_poll, list_polls

VOTE_ERROR = "Please select one option before you vote."

# 画面の endpoint と、ナビゲーションで強調する項目の対応
NAV_SECTION = {
    "show_poll_list": "Polls",
    "show_poll_detail": "Polls",
    "submit_vote": "Polls",
    "show_poll_results": "Results",
    "show_results_overview": "Results",
}


def create_app(db_path: str) -> Flask:
    """Flask アプリを作り、画面のルートとエラー処理とナビゲーションを登録する。"""
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path
    app.add_url_rule("/", "show_poll_list", show_poll_list)
    app.add_url_rule("/polls/<int:poll_id>", "show_poll_detail", show_poll_detail)
    app.add_url_rule(
        "/polls/<int:poll_id>/vote", "submit_vote", submit_vote, methods=["POST"]
    )
    app.add_url_rule(
        "/polls/<int:poll_id>/results", "show_poll_results", show_poll_results
    )
    app.add_url_rule("/results", "show_results_overview", show_results_overview)
    app.register_error_handler(404, handle_not_found)
    app.context_processor(provide_navigation)
    return app


def provide_navigation():
    """全画面のナビゲーション項目と、現在の画面の項目を返す。"""
    current = NAV_SECTION.get(request.endpoint)
    items = [
        {"label": "Polls", "endpoint": "show_poll_list"},
        {"label": "Results", "endpoint": "show_results_overview"},
    ]
    for item in items:
        item["active"] = item["label"] == current
    return {"nav_items": items}


def show_poll_list():
    """投票テーマの一覧画面を返す。"""
    polls = list_polls(current_app.config["DB_PATH"])
    return render_template("poll_list.html", polls=polls)


def show_poll_detail(poll_id: int):
    """投票テーマの質問と選択肢、投票のフォームを返す。無ければ 404。"""
    poll = get_poll(current_app.config["DB_PATH"], poll_id)
    if poll is None:
        abort(404)
    return render_template("poll_detail.html", poll=poll, error=None)


def submit_vote(poll_id: int):
    """選んだ選択肢に 1 票を記録し、結果画面へ移る。不正な入力は詳細画面に戻して知らせる。"""
    db_path = current_app.config["DB_PATH"]
    poll = get_poll(db_path, poll_id)
    if poll is None:
        abort(404)
    try:
        option_id = int(request.form.get("option_id", ""))
    except ValueError:
        return render_template("poll_detail.html", poll=poll, error=VOTE_ERROR), 400
    try:
        cast_vote(db_path, poll_id, option_id)
    except ValueError:
        return render_template("poll_detail.html", poll=poll, error=VOTE_ERROR), 400
    return redirect(url_for("show_poll_results", poll_id=poll_id, voted=1), code=303)


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
