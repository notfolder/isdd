#!/usr/bin/env bash
# One-time setup. This project has no external packages to install;
# it checks that the Node.js runtime can run the server.
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v node >/dev/null 2>&1; then
  echo "setup: node was not found. Install Node.js 24 or later." >&2
  exit 1
fi

major="$(node -p 'process.versions.node.split(".")[0]')"
if [ "$major" -lt 24 ]; then
  echo "setup: Node.js 24 or later is required (found $(node -v))." >&2
  exit 1
fi

if ! node -e "require('node:sqlite')" >/dev/null 2>&1; then
  echo "setup: node:sqlite is not available in this Node.js build." >&2
  exit 1
fi

chmod +x run.sh setup.sh
echo "setup: OK (node $(node -v); no external packages needed)."
