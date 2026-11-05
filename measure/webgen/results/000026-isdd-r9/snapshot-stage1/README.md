# Polls Website

A small website where users browse polls, cast a vote for one option, and view the results.
The interface is in English, the background is white, and the components use navy (#000080).

## Requirements

- Python 3.12 (`python3.12`, or `python3` as a fallback)
- A Chromium browser to use the site

The site itself uses only the Python standard library. The E2E tests use Playwright, which `setup.sh` installs into `.venv`.

## 起動方法 (Start)

```bash
bash setup.sh                 # run once: creates DATA_DIR, .venv, and the Chromium build for tests
PORT=8000 bash run.sh         # starts the site in the foreground; stop with Ctrl-C
```

Then open <http://127.0.0.1:8000/> in the browser.

## Settings

| Name | Meaning | Default |
|---|---|---|
| `PORT` | Port to listen on (address `127.0.0.1`) | `8000` |
| `DATA_DIR` | Folder for the SQLite database `polls.db` | `./data` |

When the database has no polls, three sample polls are added at startup so every feature can be tried at once.

## Screens

- **Polls** (`/polls`): the list of polls. Choose **Vote** to open a poll.
- **Vote** (`/polls/{id}`): choose one option and press **Submit vote**. You can vote once per poll per browser.
- **Results** (`/polls/{id}/results`): vote counts and percentages for each option.
- **Results** in the top menu (`/results`): the list of polls with their totals.

## Tests

```bash
.venv/bin/python -m pytest e2e/test_polls_unit.py                                  # unit tests
.venv/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml                     # unit and E2E tests
```

## Layout

- `app/server.py`: HTTP routes
- `app/polls.py`: poll rules (listing, voting, results)
- `app/db.py`: SQLite access and schema
- `app/seed.py`: sample data
- `app/views.py`: HTML and CSS
- `app/config.py`: reads `PORT` and `DATA_DIR`
- `docs/`: requirements, detail design, and the trace map
