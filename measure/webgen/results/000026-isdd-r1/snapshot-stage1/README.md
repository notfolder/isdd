# Polls

A small polls website. Visitors browse polls, cast one vote per choice, and view the results (counts and percentages). No login is needed.

## 起動方法 (Start)

Requirements: Python 3 (3.12 recommended). No other services are needed.

```bash
bash setup.sh                 # once: creates .venv and installs Flask
PORT=8000 bash run.sh         # starts the server in the foreground
```

Then open **http://127.0.0.1:8000** in a browser.

- `PORT` (default `8000`): port to listen on at `127.0.0.1`.
- `DATA_DIR` (default `./data`): folder that holds the SQLite file `polls.db`. It is created when missing.

On the first start the site adds three sample polls with some votes, so every feature can be tried at once. The data is kept across restarts; delete `DATA_DIR` to start over.

## Pages

- **Polls**: list of polls, with links to vote or to see the results.
- **Vote**: choose one option and press Vote.
- **Results**: vote counts and shares for one poll.
- **Results** (top menu): totals and the leading option for every poll.

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
