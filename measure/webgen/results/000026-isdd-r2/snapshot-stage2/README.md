# Polls Website

A small website where visitors browse polls, vote for one option per poll, and view the results.

## 起動方法（Start）

Requires Python 3.12 (or `python3`) and no external services.

```bash
bash setup.sh                 # once: creates .venv and installs Flask
PORT=8000 bash run.sh         # starts the site in the foreground
```

Open http://127.0.0.1:8000 in a browser. The root URL goes to the poll list.

- `PORT` (default `8000`): the port on 127.0.0.1 to listen on.
- `DATA_DIR` (default `./data`): where `polls.db` (SQLite) is stored. When the database has no polls, sample polls are added on start.

Stop the server with Ctrl+C.

## Pages

- **Polls**: the list of polls. Open a poll to see its options and vote.
- **Results**: the vote counts and percentages for each poll.

Each browser can vote once per poll (tracked with a cookie). A second vote in the same poll is refused with a message. After a vote, the options and the Vote button of that poll are disabled in that browser, and the message "You have already voted" is shown.

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -v                              # unit and integration tests
.venv/bin/python scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml   # end-to-end tests
```

The design documents are in `docs/` (`requirements.md`, `detail_design.md`, `trace_map.md`). Run `bash scripts/isdd/check.sh --strict` to check them against the code.
