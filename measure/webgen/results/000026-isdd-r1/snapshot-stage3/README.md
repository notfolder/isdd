# Surveys

A small surveys website. Visitors browse surveys, cast one vote per choice, and view the results (counts and percentages). No login is needed.

## 起動方法 (Start)

Requirements: Python 3 (3.12 recommended). No other services are needed.

```bash
bash setup.sh                 # once: creates .venv and installs Flask
PORT=8000 bash run.sh         # starts the server in the foreground
```

Then open **http://127.0.0.1:8000** in a browser.

- `PORT` (default `8000`): port to listen on at `127.0.0.1`.
- `DATA_DIR` (default `./data`): folder that holds the SQLite file `polls.db` (the file name is unchanged). It is created when missing.

On the first start the site adds three sample surveys with some votes, so every feature can be tried at once. The data is kept across restarts; delete `DATA_DIR` to start over.

## Pages

- **Surveys**: list of surveys, with links to vote or to see the results.
- **Vote**: choose one option and press Vote.
- **Results**: vote counts and shares for one survey.
- **Results** (top menu): totals and the leading option for every survey.

## Voting rule

Each browser can vote once per survey. The site keeps a browser cookie named `voter_id` for this. After a browser has voted in a survey, that survey's options and Vote button are disabled and the page shows "You have already voted". The server also refuses a second vote sent directly (HTTP 409), so it is not counted. Other surveys stay open to vote. Clearing the cookie (or using a private window) counts as a new browser. There is no login.

## Colors

The background is light yellow (`#FFFFE0`). Headers, navigation, headings, buttons, cards, and result bars are dark slate gray (`#2F4F4F`). The colors are set in `src/web/static/style.css`.

## Tests

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -t . -v      # unit tests
.venv/bin/python scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml   # end-to-end tests
```

## Layout

- `src/main.py`: startup (settings, database setup, sample data, server)
- `src/store/db.py`: SQLite storage, counting and voting
- `src/web/app.py`: pages and form handling; templates in `src/web/templates`, styles in `src/web/static`
- `docs/`: requirements, detailed design, and the trace map between design IDs and code
