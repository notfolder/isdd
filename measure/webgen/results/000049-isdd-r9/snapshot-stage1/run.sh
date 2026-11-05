#!/usr/bin/env bash
# Start the Barber Shop site in the foreground.
# Usage: PORT=8000 bash run.sh   (PORT default 8000, DATA_DIR default ./data)
set -euo pipefail
cd "$(dirname "$0")"
export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-$PWD/data}"
exec env PYTHONPATH=src python3 -m web.server
