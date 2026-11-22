#!/usr/bin/env bash
# 準備。.venv を作って依存を入れる。
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/python -m pip install -q -r requirements.txt
