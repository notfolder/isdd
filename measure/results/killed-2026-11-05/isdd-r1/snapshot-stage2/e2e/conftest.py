"""E2E テストの共通設定。空きポートと一時の DATA_DIR で本物のサーバーを起動し、Chromium を用意する。"""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class AppServer:
    def __init__(self, base_url, data_dir):
        self.base_url = base_url
        self.data_dir = data_dir


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def start_app(tmp_path):
    """本物のサーバー（python -m equipment_ledger）を一時の DATA_DIR で起動する。終わりに停止する。"""
    processes = []

    def _start(idle_timeout=1800):
        data_dir = tmp_path / "data"
        data_dir.mkdir(exist_ok=True)
        port = _free_port()
        env = dict(
            os.environ,
            PORT=str(port),
            HOST="127.0.0.1",
            DATA_DIR=str(data_dir),
            SESSION_IDLE_TIMEOUT_SECONDS=str(idle_timeout),
            PYTHONPATH=str(SRC),
        )
        log_path = tmp_path / f"server-{port}.log"
        log = open(log_path, "w", encoding="utf-8")
        process = subprocess.Popen(
            [sys.executable, "-m", "equipment_ledger"], cwd=ROOT, env=env, stdout=log, stderr=log
        )
        processes.append((process, log))
        deadline = time.time() + 20
        while time.time() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"サーバーが起動できませんでした: {log_path.read_text(encoding='utf-8')}")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                if probe.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.1)
        else:
            raise RuntimeError("サーバーが 20 秒以内に応答しませんでした")
        return AppServer(f"http://127.0.0.1:{port}", data_dir)

    yield _start
    for process, log in processes:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        log.close()


@pytest.fixture
def page():
    """Chromium のページを 1 つ用意する（テストごとに新しい Cookie）。"""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(10000)
        yield page
        browser.close()
