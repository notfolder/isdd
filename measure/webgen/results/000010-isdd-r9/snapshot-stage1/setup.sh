#!/usr/bin/env bash
# One-time setup. This app uses only the Python standard library, so there is
# nothing to install; this script checks the tools and creates the data folder.
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 (3.9 or later, 3.12 recommended) is required" >&2
  exit 1
fi
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
  echo "error: python3 must be version 3.9 or later" >&2
  exit 1
fi
echo "python3: $(python3 --version)"
if command -v node >/dev/null 2>&1; then
  echo "node: $(node --version) (not used by the server)"
else
  echo "node: not found (not required)"
fi

DATA_DIR_PATH="${DATA_DIR:-$PWD/data}"
mkdir -p "$DATA_DIR_PATH"
echo "data folder: $DATA_DIR_PATH"
echo "Setup complete. Start the site with: PORT=8000 bash run.sh"
