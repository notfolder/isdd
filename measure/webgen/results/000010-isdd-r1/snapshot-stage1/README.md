# Wheel of Fortune

A small prize website. Visitors enter a name, spin the wheel, see the prize list, and look up their own winning records. The interface is in English.

## 起動方法

Requirements: Node.js 24 or later. No external packages are needed.

```bash
bash setup.sh                 # checks Node.js 24 and node:sqlite
PORT=8000 bash run.sh         # starts the server in the foreground
```

Then open `http://127.0.0.1:8000/` in a browser (Chromium recommended).

- `PORT`: port to listen on (default `8000`).
- `DATA_DIR`: directory for the SQLite file `wheel.sqlite` (default `./data`). It is created when missing. When it is empty, sample prizes and sample winning records (for the name `Sample Player`) are added at startup.

Stop the server with Ctrl+C.

## 画面

- **Spin the Wheel**: type your name (1-30 characters) and press Spin. The wheel turns and shows the prize you won; the win is recorded under your name. The last name you used is remembered in this browser.
- **Prize List**: every prize with its chance of being won (weight divided by the total weight).
- **My Winnings**: type a name to see that name's winning records, newest first (up to 100).

The top menu appears on every screen and shows the current screen.

## テスト

```bash
node --test 'tests/unit/*.test.js'                                   # unit tests
mkdir -p e2e/results && node --test --test-reporter=junit --test-reporter-destination=e2e/results/e2e.xml 'e2e/*.test.js'   # end-to-end tests (JUnit XML in e2e/results/)
```

The end-to-end tests start the real server on a free port with a temporary data directory.

## 構成

- `src/`: server code (`server.js` entry, `routes.js` HTTP and JSON API, `spin.js` draw rules, `db.js` SQLite)
- `public/`: the pages (`index.html`, `style.css`, `app.js`)
- `tests/unit/`, `e2e/`: tests
- `docs/`: requirements, detailed design, and the trace map (design IDs to code)
- `scripts/isdd/`: consistency checks (`bash scripts/isdd/check.sh --strict`)
