#!/usr/bin/env bash
# Install dependencies for the Polls website. Run once before starting the site.
# The site itself uses only the Python standard library. The E2E test tools (pytest, Playwright)
# are installed into ./.venv so that they do not touch the system Python.
set -euo pipefail

cd "$(dirname "$0")"

PYTHON_BIN="python3"
if command -v python3.12 >/dev/null 2>&1; then
  PYTHON_BIN="python3.12"
fi
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "python3 was not found. Install Python 3.12 first." >&2
  exit 1
fi

DATA_DIR_VALUE="${DATA_DIR:-./data}"
mkdir -p "$DATA_DIR_VALUE"

if [ ! -x .venv/bin/python ]; then
  "$PYTHON_BIN" -m venv .venv
fi
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -r requirements-dev.txt
.venv/bin/python -m playwright install chromium

echo "Setup finished. Start the site with: PORT=8000 bash run.sh"
