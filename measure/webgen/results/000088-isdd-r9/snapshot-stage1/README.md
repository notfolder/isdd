# Species Database

A web site for browsing, searching, filtering and managing biological information about species.
The screens are in English. The site uses only the Python 3.12 standard library at run time; no external service is used.

## 起動方法 / How to start

Run these commands from the project root.

```bash
bash setup.sh                  # once: creates .venv and installs Playwright + Chromium for the end-to-end tests
PORT=8000 bash run.sh          # starts the web server in the foreground (Ctrl+C to stop)
```

Then open http://127.0.0.1:8000 in a Chromium-based browser.

- `PORT`: the port to listen on (default 8000).
- `DATA_DIR`: where the SQLite database `species.sqlite3` is stored (default `./data`). It is created if it does not exist.
- The first time the database is created, 12 sample species are loaded. They are not loaded again on later starts.
- There is no login. Anyone who can reach the server can add, change and delete species.

## Screens

- **Home**: totals of all species and of threatened species (VU, EN, CR).
- **Browse species**: search by scientific or common name, filter by Class, Habitat, Diet and Conservation status (all filters combine), and the results table. Click a name to see its details.
- **Species details**: every stored value, with "Back to results", "Edit" and "Delete" (Delete asks for confirmation).
- **Add species / Edit species**: the form with validation messages.

## Notes

- The sample species are for demonstration. Check conservation status, lifespan and body mass against an authoritative source before real use.
- Colors: linen background; maroon for navigation, buttons, table headers, links and focus outlines.

## Tests

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v            # unit and integration tests
.venv/bin/python scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml   # end-to-end tests (browser)
```

Design and requirements are in `docs/requirements.md` and `docs/detail_design.md`. The trace between design IDs and code is in `docs/trace_map.md`.
