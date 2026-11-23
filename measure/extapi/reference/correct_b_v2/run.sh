#!/usr/bin/env bash
cd "$(dirname "$0")/../correct_b" && REF_API_VERSION=2 exec python3 app.py
