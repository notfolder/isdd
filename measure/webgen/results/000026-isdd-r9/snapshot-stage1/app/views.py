"""HTML and CSS for every screen. Functions here only format data; they do not touch the database."""

from __future__ import annotations

from collections.abc import Sequence
from html import escape
from typing import Any

NAVY = "#000080"
WHITE = "#ffffff"

CSS = f"""
body {{ background: {WHITE}; color: {NAVY}; font-family: Arial, Helvetica, sans-serif; margin: 0; }}
header.site {{ background: {NAVY}; color: {WHITE}; padding: 12px 24px; }}
header.site .brand {{ font-size: 20px; font-weight: bold; color: {WHITE}; text-decoration: none; }}
nav.menu a {{ color: {WHITE}; margin-right: 18px; text-decoration: none; font-weight: bold; }}
nav.menu a:hover {{ text-decoration: underline; }}
main {{ padding: 24px; max-width: 880px; }}
h1, h2 {{ color: {NAVY}; }}
.cards {{ list-style: none; padding: 0; }}
.card {{ border: 2px solid {NAVY}; border-radius: 6px; padding: 14px 18px; margin-bottom: 14px; }}
.card h2 {{ margin: 0 0 6px 0; font-size: 20px; }}
.card a {{ color: {NAVY}; }}
a.button, button.button {{ background: {NAVY}; color: {WHITE}; border: none; border-radius: 4px;
  padding: 8px 16px; font-size: 15px; text-decoration: none; cursor: pointer; display: inline-block; }}
.option {{ margin: 8px 0; font-size: 17px; }}
.error {{ border: 2px solid {NAVY}; background: {WHITE}; color: {NAVY}; font-weight: bold; padding: 8px 12px; }}
.notice {{ border: 2px solid {NAVY}; color: {NAVY}; padding: 8px 12px; }}
.result-row {{ margin: 14px 0; }}
.result-label {{ font-size: 17px; margin-bottom: 4px; }}
.bar-track {{ background: {WHITE}; border: 2px solid {NAVY}; height: 22px; border-radius: 4px; }}
.bar-fill {{ background: {NAVY}; height: 100%; border-radius: 2px; }}
.muted {{ color: {NAVY}; }}
"""


def _votes(count: int) -> str:
    return f"{count} vote" if count == 1 else f"{count} votes"


def _layout(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} | Polls</title>
<style>{CSS}</style>
</head>
<body>
<header class="site">
  <a class="brand" href="/polls">Polls</a>
  <nav class="menu" aria-label="Main navigation">
    <a href="/polls">Polls</a>
    <a href="/results">Results</a>
  </nav>
</header>
<main>
{body}
</main>
</body>
</html>
"""


def poll_list_page(polls: Sequence[dict[str, Any]]) -> str:
    if not polls:
        body = "<h1>Polls</h1>\n<p>No polls yet.</p>"
    else:
        items = []
        for poll in polls:
            items.append(
                f'<li class="card"><h2><a href="/polls/{poll["id"]}">{escape(poll["title"])}</a></h2>'
                f'<p class="muted">{poll["option_count"]} options · {_votes(poll["total_votes"])}</p>'
                f'<a class="button" href="/polls/{poll["id"]}">Vote</a></li>'
            )
        body = "<h1>Polls</h1>\n<p>Browse the polls and cast your vote.</p>\n<ul class=\"cards\">\n" + "\n".join(items) + "\n</ul>"
    return _layout("Polls", body)


def poll_vote_page(poll: dict[str, Any], error: str | None = None, notice: str | None = None) -> str:
    parts = [f"<h1>{escape(poll['title'])}</h1>"]
    if poll["description"]:
        parts.append(f"<p>{escape(poll['description'])}</p>")
    if error:
        parts.append(f'<p class="error" role="alert">{escape(error)}</p>')
    if notice:
        parts.append(f'<p class="notice">{escape(notice)}</p>')
        parts.append(f'<p><a class="button" href="/polls/{poll["id"]}/results">View results</a></p>')
    parts.append(f'<form method="post" action="/polls/{poll["id"]}/vote">')
    for option in poll["options"]:
        parts.append(
            f'<div class="option"><label><input type="radio" name="option" value="{option["id"]}"> '
            f'{escape(option["label"])}</label></div>'
        )
    parts.append('<p><button class="button" type="submit">Submit vote</button> '
                 f'<a class="button" href="/polls/{poll["id"]}/results">View results</a></p>')
    parts.append("</form>")
    return _layout(poll["title"], "\n".join(parts))


def poll_results_page(data: dict[str, Any]) -> str:
    poll = data["poll"]
    parts = [f"<h1>{escape(poll['title'])}</h1>"]
    if poll["description"]:
        parts.append(f"<p>{escape(poll['description'])}</p>")
    if data["total_votes"] == 0:
        parts.append('<p class="muted">No votes yet.</p>')
    else:
        parts.append(f'<p class="muted">Total votes: {data["total_votes"]}</p>')
    for option in data["options"]:
        parts.append(
            '<div class="result-row">'
            f'<div class="result-label">{escape(option["label"])}: {option["votes"]} votes ({option["percent"]}%)</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width: {option["percent"]}%"></div></div>'
            "</div>"
        )
    parts.append(f'<p><a class="button" href="/polls/{poll["id"]}">Vote in this poll</a> '
                 '<a class="button" href="/results">All results</a></p>')
    return _layout(f"Results: {poll['title']}", "\n".join(parts))


def results_list_page(items: Sequence[dict[str, Any]]) -> str:
    if not items:
        body = "<h1>Results</h1>\n<p>No polls yet.</p>"
    else:
        rows = []
        for item in items:
            rows.append(
                f'<li class="card"><h2>{escape(item["title"])}</h2>'
                f'<p class="muted">Total votes: {item["total_votes"]}</p>'
                f'<a class="button" href="/polls/{item["id"]}/results">View results</a></li>'
            )
        body = "<h1>Results</h1>\n<ul class=\"cards\">\n" + "\n".join(rows) + "\n</ul>"
    return _layout("Results", body)


def message_page(title: str, message: str) -> str:
    body = f"<h1>{escape(title)}</h1>\n<p>{escape(message)}</p>\n<p><a class=\"button\" href=\"/polls\">Back to polls</a></p>"
    return _layout(title, body)
