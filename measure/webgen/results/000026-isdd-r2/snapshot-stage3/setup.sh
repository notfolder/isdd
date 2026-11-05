#!/usr/bin/env bash
# Install the dependencies into ./.venv. Safe to run more than once.
set -euo pipefail
cd "$(dirname "$0")"

if command -v python3.12 >/dev/null 2>&1; then
  PY=python3.12
else
  PY=python3
fi

if [ ! -x .venv/bin/python ]; then
  "$PY" -m venv .venv
fi

.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -r requirements.txt
echo "setup complete: $(.venv/bin/python --version) with $(.venv/bin/python -c 'from importlib.metadata import version; print("Flask " + version("flask"))')"
