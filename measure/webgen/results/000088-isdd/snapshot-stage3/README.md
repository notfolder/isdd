# Species Database

A small web site for browsing, searching, filtering, and managing biological information about species.

## 起動方法 (Start)

Requirements: Python 3.12 (`python3`). Nothing else is needed; the dependencies are installed into `.venv`.

```bash
bash setup.sh                 # install dependencies (run once)
PORT=8000 bash run.sh         # start the web server in the foreground
```

Open http://127.0.0.1:8000 in a browser. Stop the server with Ctrl+C.

- `PORT`: port to listen on (default `8000`). The server only listens on `127.0.0.1`.
- `DATA_DIR`: directory that holds the SQLite database `species.db` (default `./data`). It is created if missing.

When the database is empty, 12 sample species are added at start-up, so every feature can be tried immediately.

## Features

- **Browse**: the species list on the start page, and a detail page for each species. The list can be sorted by name, A to Z (default) or Z to A ("Sort" menu). The detail page shows all stored fields, including when the species was added and last updated (UTC).
- **Search**: keyword search over scientific name, common name, and description (case-insensitive, partial match).
- **Filter**: by kingdom, habitat, diet, and conservation status. Search and filters combine with AND. "Clear" resets them.
- **Manage**: add ("Add species" in the menu), edit, and delete species. Deleting asks for confirmation. Name, Habitat and Diet are required; the other fields are optional. A scientific name, when given, must be unique.

The colours are a honeydew background with dark olive green components (see `app/static/style.css`).

There are no user accounts; anyone who can open the page can change the data.

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -t . -v                  # unit tests
.venv/bin/python scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml   # end-to-end tests (starts real servers)
```

## Project layout

- `app/`: the Flask application (routes, validation, repository, SQLite access, templates, stylesheet)
- `tests/`: unit tests
- `e2e/`: end-to-end tests over HTTP
- `docs/`: requirements, detailed design, and the trace map between design IDs and code
