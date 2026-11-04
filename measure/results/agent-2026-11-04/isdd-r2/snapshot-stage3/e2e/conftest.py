"""E2E テストの共通部品。アプリを一時 DATA_DIR と空きポートで起動する。"""

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def start_app(tmp_path):
    """アプリを起動し、基準 URL を返す関数を渡す。テスト後に止める。"""
    procs = []

    def _start(idle_seconds=None) -> str:
        port = _free_port()
        env = dict(os.environ, PORT=str(port), HOST="127.0.0.1", DATA_DIR=str(tmp_path / "data"))
        if idle_seconds is not None:
            env["SESSION_IDLE_TIMEOUT_SECONDS"] = str(idle_seconds)
        proc = subprocess.Popen(
            [sys.executable, "-m", "equipment_ledger"],
            cwd=ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        procs.append(proc)
        base = f"http://127.0.0.1:{port}"
        deadline = time.time() + 30
        while True:
            try:
                urllib.request.urlopen(base + "/", timeout=2).read()
                return base
            except Exception:
                if time.time() > deadline:
                    raise
                time.sleep(0.2)

    yield _start
    for proc in procs:
        proc.terminate()
        proc.wait(timeout=10)
