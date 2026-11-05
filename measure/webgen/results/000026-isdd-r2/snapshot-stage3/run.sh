#!/usr/bin/env bash
# Start the polls website in the foreground on 127.0.0.1.
# Usage: PORT=8000 bash run.sh   (PORT defaults to 8000; DATA_DIR defaults to ./data)
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  echo "The environment is missing. Run: bash setup.sh" >&2
  exit 1
fi

export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-$(pwd)/data}"
exec .venv/bin/python src/server.py
