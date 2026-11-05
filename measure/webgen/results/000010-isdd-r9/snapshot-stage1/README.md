# Wheel of Fortune

A small website where visitors spin a prize wheel. Spin the wheel, see the prize list
with chances, and check your own winning records.

## Requirements

- Python 3.9 or later (3.12 recommended). No extra packages are needed.
- Node.js is optional and is not used by the server.
- A Chromium-based browser to use the site.

## 起動方法 (Start)

```bash
bash setup.sh                 # once: checks Python and creates the data folder
PORT=8000 bash run.sh         # starts the site in the foreground
```

Open http://127.0.0.1:8000 in your browser. Stop the server with Ctrl+C.

| Variable | Default | Meaning |
|---|---|---|
| `PORT` | `8000` | Port to listen on at 127.0.0.1 |
| `DATA_DIR` | `./data` | Folder for the SQLite database (`wheel.sqlite3`), created if missing |

When the database has no prizes, the site inserts 8 sample prizes at start-up.

## Pages

- **Spin**: spin the wheel. Enter an optional name (empty means `Guest`, up to 30 characters).
  Winning results are saved to your winning records; "No prize" results are not.
- **Prizes**: the prize list with the chance of each prize.
- **My Winnings**: your own winning records, newest first.

Your records belong to your browser. The site stores a random anonymous ID in a cookie
(`wof_player`); there is no login.

## Tests

```bash
python3 -m unittest discover -s tests -v                              # unit tests
python3 scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml   # end-to-end scenarios
```

## Design documents

The requirements and design are in `docs/requirements.md` and `docs/detail_design.md`.
The mapping from design IDs to code is in `docs/trace_map.md`.
