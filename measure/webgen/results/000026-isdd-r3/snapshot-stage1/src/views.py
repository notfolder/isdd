"""HTML generation for every page. Every user-visible string is escaped."""

from html import escape

NAVY = "#000080"

STYLE = """
body { background: #ffffff; color: #1a1a1a; font-family: Arial, Helvetica, sans-serif;
       margin: 0; line-height: 1.5; }
.nav { background: #000080; padding: 12px 24px; }
.nav a { color: #ffffff; text-decoration: none; margin-right: 24px; font-weight: bold; }
.nav a:hover { text-decoration: underline; }
main { max-width: 760px; margin: 0 auto; padding: 24px; }
h1, h2 { color: #000080; }
a { color: #000080; }
.card { border: 2px solid #000080; border-radius: 6px; padding: 16px; margin-bottom: 16px; }
.button { background: #000080; color: #ffffff; border: none; border-radius: 4px;
          padding: 8px 16px; font-size: 15px; cursor: pointer; text-decoration: none;
          display: inline-block; }
.error { color: #000080; border: 2px solid #000080; border-radius: 6px; padding: 8px 12px;
         font-weight: bold; }
.notice { color: #ffffff; background: #000080; border-radius: 6px; padding: 8px 12px; }
.option-row { margin: 8px 0; }
.bar-track { background: #e6e8f2; border-radius: 4px; height: 18px; width: 100%; }
.bar-fill { background: #000080; border-radius: 4px; height: 18px; }
table { border-collapse: collapse; width: 100%; }
td, th { text-align: left; padding: 6px 8px; border-bottom: 1px solid #000080; }
"""


def render_layout(title, body):
    """Return a full HTML page with the given title and body HTML, including the navigation menu."""
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{escape(title)} - Polls</title>\n<style>{STYLE}</style>\n</head>\n<body>\n"
        f"{render_navigation_menu()}\n<main>\n{body}\n</main>\n</body>\n</html>\n"
    )


def render_navigation_menu():
    """Return the navigation bar that links to Polls and Results on every page."""
    return (
        "<nav class=\"nav\" aria-label=\"Main navigation\">"
        "<a href=\"/\">Polls</a><a href=\"/results\">Results</a></nav>"
    )


def _percent_text(percent):
    """Format a percentage with one decimal place, for example 41.7%."""
    return f"{percent:.1f}%"


def _result_rows(options):
    """Return the HTML rows of a result table: option, votes, percent and a bar."""
    rows = []
    for option in options:
        rows.append(
            "<tr>"
            f"<td>{escape(option['text'])}</td>"
            f"<td>{option['votes']}</td>"
            f"<td>{_percent_text(option['percent'])}</td>"
            "<td style=\"width:40%\"><div class=\"bar-track\">"
            f"<div class=\"bar-fill\" style=\"width:{option['percent']}%\"></div>"
            "</div></td></tr>"
        )
    return "".join(rows)


def render_poll_list(polls):
    """Return the poll list page: each poll with its option count, totals and links."""
    if not polls:
        body = "<h1>Polls</h1><p>No polls available.</p>"
        return render_layout("Polls", body)
    cards = []
    for poll in polls:
        cards.append(
            "<div class=\"card\">"
            f"<h2>{escape(poll['question'])}</h2>"
            f"<p>Options: {poll['option_count']} &middot; Total votes: {poll['total_votes']}</p>"
            f"<p><a class=\"button\" href=\"/polls/{poll['id']}\">Vote</a> "
            f"<a href=\"/polls/{poll['id']}/results\">View results</a></p>"
            "</div>"
        )
    body = "<h1>Polls</h1>" + "".join(cards)
    return render_layout("Polls", body)


def render_vote_page(poll, options, error=None):
    """Return the voting page: the question, one radio button per option and the submit button.

    error, when given, is shown above the form (for example "Please select an option.").
    """
    parts = [f"<h1>{escape(poll['question'])}</h1>"]
    if error:
        parts.append(f"<p class=\"error\" role=\"alert\">{escape(error)}</p>")
    radios = []
    for option in options:
        radios.append(
            "<div class=\"option-row\"><label>"
            f"<input type=\"radio\" name=\"option_id\" value=\"{option['id']}\"> "
            f"{escape(option['text'])}</label></div>"
        )
    parts.append(
        f"<form method=\"post\" action=\"/polls/{poll['id']}/vote\">"
        + "".join(radios)
        + "<p><button class=\"button\" type=\"submit\">Submit vote</button></p></form>"
    )
    parts.append("<p><a href=\"/\">Back to polls</a></p>")
    return render_layout(poll["question"], "\n".join(parts))


def render_poll_results(result, notice=False):
    """Return the results page of one poll.

    result is the dict from PollService.get_poll_results. notice=True shows
    the "Your vote has been recorded." message after voting.
    """
    poll = result["poll"]
    parts = [f"<h1>{escape(poll['question'])}</h1>"]
    if notice:
        parts.append("<p class=\"notice\" role=\"status\">Your vote has been recorded.</p>")
    parts.append(
        "<table><thead><tr><th>Option</th><th>Votes</th><th>Share</th><th>Chart</th></tr></thead>"
        f"<tbody>{_result_rows(result['options'])}</tbody></table>"
    )
    parts.append(f"<p>Total votes: {result['total']}</p>")
    parts.append(
        f"<p><a href=\"/polls/{poll['id']}\">Vote on this poll</a> &middot; "
        "<a href=\"/results\">All results</a></p>"
    )
    return render_layout(poll["question"], "\n".join(parts))


def render_all_results(results):
    """Return the results overview page with the results of every poll.

    results is a list of dicts from PollService.get_poll_results.
    """
    if not results:
        return render_layout("Results", "<h1>Results</h1><p>No polls available.</p>")
    sections = ["<h1>Results</h1>"]
    for result in results:
        poll = result["poll"]
        sections.append(
            "<div class=\"card\">"
            f"<h2>{escape(poll['question'])}</h2>"
            "<table><thead><tr><th>Option</th><th>Votes</th><th>Share</th><th>Chart</th></tr></thead>"
            f"<tbody>{_result_rows(result['options'])}</tbody></table>"
            f"<p>Total votes: {result['total']} &middot; "
            f"<a href=\"/polls/{poll['id']}/results\">Details</a></p>"
            "</div>"
        )
    return render_layout("Results", "\n".join(sections))


def render_not_found(message="Page not found."):
    """Return the 404 page with the given message."""
    body = f"<h1>Not found</h1><p>{escape(message)}</p><p><a href=\"/\">Back to polls</a></p>"
    return render_layout("Not found", body)
