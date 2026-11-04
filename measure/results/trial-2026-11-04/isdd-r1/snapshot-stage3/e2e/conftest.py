"""E2E の共通の準備。run.sh を一時の PORT と DATA_DIR で起動し、Playwright のブラウザを用意する。"""

import os
import socket
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@contextmanager
def run_server(data_dir: Path, idle_timeout: int = 1800):
    """bash run.sh を起動し、待ち受けが始まったら基底の URL を返す。終わったら止める。"""
    port = _free_port()
    env = dict(os.environ)
    env.update({"PORT": str(port), "DATA_DIR": str(data_dir), "SESSION_IDLE_TIMEOUT_SECONDS": str(idle_timeout)})
    log_path = data_dir / "server.log"
    with open(log_path, "w", encoding="utf-8") as log:
        proc = subprocess.Popen(["bash", "run.sh"], cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.time() + 15
            while time.time() < deadline:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    if sock.connect_ex(("127.0.0.1", port)) == 0:
                        break
                time.sleep(0.2)
            else:
                raise RuntimeError("サーバーが起動しませんでした")
            yield f"http://127.0.0.1:{port}"
        finally:
            proc.terminate()
            proc.wait(timeout=10)


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def data_dir(tmp_path):
    path = tmp_path / "data"
    path.mkdir()
    return path


@pytest.fixture
def server(data_dir):
    with run_server(data_dir) as base:
        yield base


@pytest.fixture
def new_page(browser):
    """新しい（Cookie の無い）ページを返す。テストの終わりに閉じる。"""
    contexts = []

    def make():
        context = browser.new_context()
        contexts.append(context)
        page = context.new_page()
        page.on("dialog", lambda dialog: dialog.accept())
        return page

    yield make
    for context in contexts:
        context.close()
