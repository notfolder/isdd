#!/usr/bin/env bash
# Prepares the barbershop site. The app uses only the Python 3 standard library,
# so there is nothing to download; this checks the tools and creates the data directory.
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required (3.9 or newer; 3.12 recommended)." >&2
  exit 1
fi

python3 -c "import ast,sys; ast.parse(open('app.py').read())"

DATA_DIR_PATH="${DATA_DIR:-$(pwd)/data}"
mkdir -p "$DATA_DIR_PATH"

echo "Setup complete. Start the site with: PORT=8000 bash run.sh"
