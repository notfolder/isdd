#!/usr/bin/env bash
# 起動。PORT（既定 8000）で待ち受ける。データは DATA_DIR（既定 data）。
cd "$(dirname "$0")"
exec .venv/bin/python -m flask --app wsgi run --host 127.0.0.1 --port "${PORT:-8000}"
