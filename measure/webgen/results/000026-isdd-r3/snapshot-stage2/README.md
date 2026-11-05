# Polls Website

A small website where visitors browse polls, vote for one option, and view the results.
No login is needed. Data is stored in SQLite under `DATA_DIR`.

## 起動方法 / How to start

Requirements: Python 3.12 (`python3`). No third-party packages are needed.

```bash
bash setup.sh                 # checks Python and creates DATA_DIR
PORT=8000 bash run.sh         # starts the server in the foreground (Ctrl+C to stop)
```

Open http://127.0.0.1:8000 in a browser.

| Variable | Meaning | Default |
|---|---|---|
| `PORT` | Port to listen on (127.0.0.1) | `8000` |
| `DATA_DIR` | Directory for `polls.db` | `./data` |

When `DATA_DIR` has no polls yet, three sample polls with some votes are created on startup. A database created before the one-vote rule gets the `ballots` table added automatically.

## Screens

- **Polls** (`/`): the list of polls. Use *Vote* to open a poll, or *View results*.
- **Vote** (`/polls/<id>`): choose one option and press *Submit vote*. If nothing is selected, the page shows "Please select an option."
  Each poll accepts **one vote per browser**. After a browser has voted, the options and the button are disabled and the page shows "You have already voted." A repeated vote, even a direct POST, is not counted. The browser is identified by the `voter_id` cookie (HttpOnly, one year). Clearing the cookies makes the browser count as new.
- **Results** (`/polls/<id>/results`): the counts and shares of one poll. Shown after a vote.
- **Results** (`/results`): the results of all polls.

The navigation bar at the top of every page links to Polls and Results.

Colours: the background is light yellow (`#FFFFE0`) and the components (navigation bar, headings, buttons, cards, table lines, bars) are dark slate gray (`#2F4F4F`).

## Tests

```bash
python3 -m unittest discover -s tests/unit -p "test_*.py"          # unit tests
python3 scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml   # end-to-end tests
```

The end-to-end tests start their own server on a free port with a temporary data directory.

## Design documents

- `docs/requirements.md`: requirements
- `docs/detail_design.md`: detailed design
- `docs/trace_map.md`: mapping from design IDs to code
