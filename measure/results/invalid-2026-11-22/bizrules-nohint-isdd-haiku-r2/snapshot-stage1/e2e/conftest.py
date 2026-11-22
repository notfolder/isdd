"""E2E テストの共通設定。テストごとに一時フォルダの DATA_DIR でサーバーを起動し、終わったら止める。

サーバーは、このテストが起動した子プロセス（PID）だけを止める。
"""

import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SERVER_SCRIPT = ROOT / "src" / "main.py"
STARTUP_TIMEOUT_SECONDS = 30


def free_port() -> int:
    """空いている TCP ポートを 1 つ返す。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Server:
    """起動したサーバーの情報。"""

    def __init__(self, base_url: str, port: int, data_dir: Path) -> None:
        self.base_url = base_url
        self.port = port
        self.data_dir = data_dir

    def url(self, path: str) -> str:
        """パスを絶対 URL にする。"""
        return self.base_url + path


@pytest.fixture
def server(tmp_path):
    """一時フォルダの DATA_DIR でサーバーを起動する。テストの終わりに、この子プロセスだけを止める。"""
    port = free_port()
    data_dir = tmp_path / "data"
    env = dict(os.environ, PORT=str(port), DATA_DIR=str(data_dir))
    proc = subprocess.Popen([sys.executable, str(SERVER_SCRIPT)], env=env, cwd=str(ROOT),
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    base_url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    while True:
        try:
            with urllib.request.urlopen(base_url + "/", timeout=2):
                break
        except (urllib.error.URLError, ConnectionError, OSError):
            if proc.poll() is not None:
                raise RuntimeError("サーバーが起動できませんでした: " + proc.stderr.read().decode("utf-8", "replace"))
            if time.monotonic() > deadline:
                proc.terminate()
                raise RuntimeError("サーバーの起動がタイムアウトしました")
            time.sleep(0.2)
    try:
        yield Server(base_url, port, data_dir)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


@pytest.fixture(scope="session")
def browser():
    """Chromium（ヘッドレス）をテスト全体で 1 つ起動する。"""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    """テストごとに新しいブラウザの文脈（Cookie を持たない）を作る。"""
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(10000)
    yield page
    context.close()
