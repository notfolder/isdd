#!/usr/bin/env bash
# One-time preparation. Safe to run again.
#  - creates the .venv virtual environment
#  - installs the test tools in requirements-dev.txt (Playwright)
#  - installs the Chromium browser used by the end-to-end tests
# The web server itself uses only the Python standard library, so run.sh does not need this.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
cd "$ROOT"

"$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' \
  || { echo "Python 3.9 or later is required (found: $("$PYTHON" --version 2>&1))" >&2; exit 1; }

if [ ! -x .venv/bin/python ]; then
  "$PYTHON" -m venv .venv
fi
.venv/bin/python -m pip install --quiet -r requirements-dev.txt
.venv/bin/python -m playwright install chromium

mkdir -p data
echo "Setup complete. Start the site with: PORT=8000 bash run.sh"
