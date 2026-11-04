"""隠しテストの準備処理。契約（measure/contract.md）に従って、テストごとに新しいデータでアプリを起動し、終わったら止める。

アプリの場所は環境変数 MEASURE_APP_DIR。`bash run.sh` を PORT・DATA_DIR・SESSION_IDLE_TIMEOUT_SECONDS 付きで起動する。
前提データは画面操作で入れる（support/seed.py）。実装の中身（DB・フレームワーク）には触れない。
"""

import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from contextlib import contextmanager
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from support.seed import Seeder  # noqa: E402

APP_DIR = Path(os.environ["MEASURE_APP_DIR"]).resolve()
READY_SECONDS = 90


class AppServer:
    def __init__(self, base_url: str, browser) -> None:
        self.base_url = base_url
        self._browser = browser

    def seed(self, data: dict) -> None:
        Seeder(self.base_url, self._browser).seed(data)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@contextmanager
def run_app(browser, session_timeout=None):
    with tempfile.TemporaryDirectory() as tmp:
        port = _free_port()
        env = dict(os.environ, DATA_DIR=f"{tmp}/data", PORT=str(port))
        env.pop("PYTHONPATH", None)
        env.pop("VIRTUAL_ENV", None)
        if session_timeout is not None:
            env["SESSION_IDLE_TIMEOUT_SECONDS"] = str(session_timeout)
        log_path = Path(tmp) / "app.log"
        log = open(log_path, "w")
        proc = subprocess.Popen(["bash", "run.sh"], cwd=APP_DIR, env=env, stdout=log, stderr=subprocess.STDOUT,
                                start_new_session=True)
        base_url = f"http://127.0.0.1:{port}"
        try:
            deadline = time.monotonic() + READY_SECONDS
            while True:
                try:
                    urllib.request.urlopen(f"{base_url}/", timeout=2)
                    break
                except Exception:
                    if proc.poll() is not None or time.monotonic() > deadline:
                        log.flush()
                        raise RuntimeError("アプリが起動しない:\n" + log_path.read_text(errors="replace")[-3000:])
                    time.sleep(0.3)
            yield AppServer(base_url, browser)
        finally:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
                proc.wait(timeout=10)
            except Exception:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except Exception:
                    pass
            log.close()


@pytest.fixture
def app(browser):
    with run_app(browser) as server:
        yield server


@pytest.fixture
def app_with_short_session(browser):
    with run_app(browser, session_timeout=6) as server:
        yield server


@pytest.fixture
def new_page(browser):
    contexts = []

    def make():
        context = browser.new_context()
        contexts.append(context)
        return context.new_page()

    yield make
    for context in contexts:
        context.close()
