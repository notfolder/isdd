#!/usr/bin/env bash
# Start the Polls web server in the foreground. Usage: PORT=8000 bash run.sh
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "Run 'bash setup.sh' first." >&2
  exit 1
fi
export PORT="${PORT:-8000}"
exec .venv/bin/python -m app
