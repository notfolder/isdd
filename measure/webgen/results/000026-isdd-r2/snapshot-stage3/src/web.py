"""HTTP routes and HTML pages for the survey site."""
from flask import Blueprint, abort, current_app, g, make_response, redirect, render_template, request, url_for

import db
import polls
import voter

bp = Blueprint("web", __name__)


def _db():
    """Return the request's database connection, opening it on first use."""
    if "db" not in g:
        g.db = db.get_db(current_app.config["DATA_DIR"])
    return g.db


def _attach_voter_cookie(response, token):
    """Set the voter cookie on the response."""
    response.set_cookie(
        voter.COOKIE_NAME,
        token,
        max_age=voter.COOKIE_MAX_AGE_SECONDS,
        httponly=True,
        samesite="Lax",
    )
    return response


@bp.teardown_app_request
def _close_db(exc):
    """Close the request's database connection, if one was opened."""
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


@bp.route("/")
def root_redirect():
    """Send the visitor from the root URL to the survey list."""
    return redirect(url_for("web.poll_list_page"), code=302)


@bp.route("/polls", defaults={"rest": ""})
@bp.route("/polls/<path:rest>")
def legacy_poll_redirect(rest):
    """Send a visitor who opens an old /polls address to the same address under /surveys."""
    target = "/surveys" + ("/" + rest if rest else "")
    return redirect(target, code=302)


@bp.route("/surveys")
def poll_list_page():
    """Show every survey with its option count and total votes."""
    return render_template("poll_list.html", active="polls", polls=polls.list_polls(_db()))


@bp.route("/surveys/<int:poll_id>")
def poll_detail_page(poll_id):
    """Show one poll with its options and the vote form. The form is disabled when this browser has already voted."""
    conn = _db()
    poll = polls.get_poll(conn, poll_id)
    if poll is None:
        abort(404)
    voted = polls.has_voted(conn, poll_id, voter.get_voter_token(request.cookies))
    return render_template("poll_detail.html", active="polls", poll=poll, voted=voted, error=None)


@bp.route("/surveys/<int:poll_id>/vote", methods=["POST"])
def cast_vote_action(poll_id):
    """Record the selected option, then show the results; re-show the poll with a message on refusal."""
    conn = _db()
    poll = polls.get_poll(conn, poll_id)
    if poll is None:
        abort(404)

    token = voter.get_voter_token(request.cookies)
    new_token = token is None
    if new_token:
        token = voter.issue_voter_token()

    try:
        polls.cast_vote(conn, poll_id, request.form.get("option_id"), token)
    except polls.VoteError as refusal:
        already_voted = refusal.code == polls.ALREADY_VOTED
        status = 409 if already_voted else 400
        voted = polls.has_voted(conn, poll_id, token)
        html = render_template(
            "poll_detail.html",
            active="polls",
            poll=poll,
            voted=voted,
            error=None if already_voted else refusal.message,
        )
        response = make_response(html, status)
    else:
        response = redirect(url_for("web.poll_results_page", poll_id=poll_id), code=303)

    if new_token:
        _attach_voter_cookie(response, token)
    return response


@bp.route("/surveys/<int:poll_id>/results")
def poll_results_page(poll_id):
    """Show the vote counts and percentages of one survey."""
    result = polls.get_results(_db(), poll_id)
    if result is None:
        abort(404)
    return render_template("poll_results.html", active="results", result=result)


@bp.route("/results")
def results_list_page():
    """Show every survey with its total votes and a link to its results."""
    return render_template(
        "results_list.html", active="results", summaries=polls.list_poll_summaries(_db())
    )
