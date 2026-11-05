# Survey Website

A small website where visitors browse surveys, vote for one option per survey, and view the results.

## 起動方法（Start）

Requires Python 3.12 (or `python3`) and no external services.

```bash
bash setup.sh                 # once: creates .venv and installs Flask
PORT=8000 bash run.sh         # starts the site in the foreground
```

Open http://127.0.0.1:8000 in a browser. The root URL goes to the survey list.

- `PORT` (default `8000`): the port on 127.0.0.1 to listen on.
- `DATA_DIR` (default `./data`): where `polls.db` (SQLite) is stored. When the database has no surveys, sample surveys are added on start.

Stop the server with Ctrl+C.

## Pages

- **Surveys**: the list of surveys. Open a survey to see its options and vote.
- **Results**: the vote counts and percentages for each survey. The addresses are `/surveys`, `/surveys/<id>`, and `/surveys/<id>/results`; old `/polls` addresses are redirected to them.

Each browser can vote once per survey (tracked with a cookie). A second vote in the same survey is refused with a message. After a vote, the options and the Vote button of that survey are disabled in that browser, and the message "You have already voted in this survey." is shown.

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -v                              # unit and integration tests
.venv/bin/python scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml   # end-to-end tests
```

The design documents are in `docs/` (`requirements.md`, `detail_design.md`, `trace_map.md`). Run `bash scripts/isdd/check.sh --strict` to check them against the code.
