#!/usr/bin/env bash
# Prepares the project. SpeciesBase uses only the Python 3 standard library
# (sqlite3, http.server), so there are no packages to download.
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found" >&2
  exit 1
fi
python3 -c "import sqlite3, http.server, json, html, urllib.parse" 
DATA_DIR="${DATA_DIR:-$PWD/data}"
mkdir -p "$DATA_DIR"
echo "Python $(python3 --version 2>&1) OK. Data directory: $DATA_DIR"
