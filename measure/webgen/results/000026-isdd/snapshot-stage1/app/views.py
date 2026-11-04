"""Routes and page rendering for the Polls website."""

import secrets
from pathlib import Path
import re
from datetime import datetime, timezone
from typing import Optional

from flask import Blueprint, Response, current_app, g, make_response, redirect, render_template, request, url_for

from .database import open_database
from .repository import PollRepository
from .voting import InvalidVote, PollNotFound, VotingService

bp = Blueprint("polls", __name__)

VOTER_COOKIE = "voter_id"
VOTER_COOKIE_MAX_AGE = 365 * 24 * 60 * 60
VOTER_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


def _conn():
    """Open one database connection per request."""
    if "conn" not in g:
        g.conn = open_database(Path(current_app.config["DB_PATH"]))
    return g.conn


@bp.teardown_app_request
def _close_conn(_exc: Optional[BaseException]) -> None:
    conn = g.pop("conn", None)
    if conn is not None:
        conn.close()


def identify_voter(req) -> tuple[str, bool]:
    """Return (voter_id, is_new). A valid voter_id cookie is reused; otherwise a new 32-character id is made."""
    value = req.cookies.get(VOTER_COOKIE, "")
    if VOTER_ID_PATTERN.match(value):
        return value, False
    return secrets.token_hex(16), True


def _set_voter_cookie(resp: Response, voter_id: str) -> Response:
    resp.set_cookie(
        VOTER_COOKIE,
        voter_id,
        max_age=VOTER_COOKIE_MAX_AGE,
        httponly=True,
        samesite="Lax",
    )
    return resp


@bp.get("/")
def index() -> str:
    """List all polls."""
    polls = PollRepository(_conn()).list_polls()
    return render_template("polls.html", polls=polls)


@bp.get("/polls/<int:poll_id>")
def poll_page(poll_id: int):
    """Show the vote form, or the results when this browser has already voted.

    A missing poll returns the poll page with "Poll not found." and status 404.
    """
    conn = _conn()
    repo = PollRepository(conn)
    poll = repo.get_poll(poll_id)
    if poll is None:
        return render_template("poll.html", poll=None, options=[], result=None, voted=False,
                               error="Poll not found.", thanks=False), 404
    voter_id, _is_new = identify_voter(request)
    voted = voter_id is not None and repo.find_vote(poll_id, voter_id) is not None
    result = VotingService(conn).get_poll_result(poll_id) if voted else None
    options = repo.list_options(poll_id)
    thanks = request.args.get("thanks") == "1"
    return render_template("poll.html", poll=poll, options=options, result=result, voted=voted,
                           error=None, thanks=thanks)


@bp.post("/polls/<int:poll_id>/vote")
def vote(poll_id: int):
    """Record a vote, then redirect to the poll page (which shows the results)."""
    voter_id, is_new = identify_voter(request)
    raw = request.form.get("option_id", "")
    option_id = int(raw) if raw.isdigit() else None
    voted_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        VotingService(_conn()).cast_vote(poll_id, option_id, voter_id, voted_at)
    except PollNotFound:
        resp = make_response(poll_page(poll_id)[0], 404)
        return _set_voter_cookie(resp, voter_id) if is_new else resp
    except InvalidVote as exc:
        conn = _conn()
        repo = PollRepository(conn)
        poll = repo.get_poll(poll_id)
        result = None
        resp = make_response(render_template(
            "poll.html", poll=poll, options=repo.list_options(poll_id), result=result,
            voted=False, error=exc.message, thanks=False), 400)
        return _set_voter_cookie(resp, voter_id) if is_new else resp
    resp = redirect(url_for("polls.poll_page", poll_id=poll_id, thanks=1), code=303)
    return _set_voter_cookie(resp, voter_id) if is_new else resp


@bp.get("/results")
def results() -> str:
    """Show the results of all polls."""
    all_results = VotingService(_conn()).get_all_results()
    return render_template("results.html", results=all_results)
