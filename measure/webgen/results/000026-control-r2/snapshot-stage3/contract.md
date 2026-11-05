# Contract for the website (both arms receive this)

The website is started and judged automatically. Follow this contract; anything not written here is up to you.

- Put `setup.sh` and `run.sh` in the project root. `bash setup.sh` installs dependencies (run once before judging; network access is allowed here). `bash run.sh` starts the web server and serves the site at `http://127.0.0.1:$PORT` (environment variable `PORT`, default 8000). It must keep running in the foreground until killed.
- Data (database files, uploads) goes under the directory given by the environment variable `DATA_DIR` (create it if missing). When it is empty the site must still start and show sensible sample content (for example sample prizes, polls or species) so that every feature can be tried immediately.
- Available tooling: Python 3.12 (`python3`) and Node.js 24 (`node`, `npm`). Use free libraries only, no external services or paid APIs. SQLite or JSON files are fine for storage. The site must work in a Chromium browser.
- The user interface language is English. The site is judged by a person operating a browser from the root URL, following the natural-language instructions of the request; keep navigation obvious (a visible navigation menu with the main sections).
