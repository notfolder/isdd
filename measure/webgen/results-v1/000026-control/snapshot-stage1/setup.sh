#!/usr/bin/env bash
# Installs dependencies. This site uses only the Python standard library,
# so this step only checks the interpreters and prepares the data directory.
set -euo pipefail
cd "$(dirname "$0")"
python3 -c 'import sys; assert sys.version_info >= (3, 9), sys.version'
node --version >/dev/null 2>&1 || true
mkdir -p "${DATA_DIR:-$(pwd)/data}"
echo "Setup complete."
