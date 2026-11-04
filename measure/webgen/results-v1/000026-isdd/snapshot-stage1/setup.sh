#!/usr/bin/env bash
# Install the Python dependencies into .venv (run once before judging).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
if [ ! -x .venv/bin/python ]; then
  "$PY" -m venv .venv
fi
.venv/bin/python -m pip install --quiet -r requirements.txt
echo "Setup complete. Start the site with: PORT=8000 bash run.sh"
