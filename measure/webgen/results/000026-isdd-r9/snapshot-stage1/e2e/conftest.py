"""Start the site on a free port with a fresh DATA_DIR for each E2E test."""

import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def base_url():
    port = _free_port()
    with tempfile.TemporaryDirectory() as data_dir:
        env = dict(os.environ, PORT=str(port), DATA_DIR=data_dir)
        proc = subprocess.Popen(
            [sys.executable, str(ROOT / "app" / "server.py")],
            env=env,
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        url = f"http://127.0.0.1:{port}"
        try:
            deadline = time.time() + 20
            while True:
                try:
                    urllib.request.urlopen(url + "/polls", timeout=1)
                    break
                except Exception:
                    if time.time() > deadline or proc.poll() is not None:
                        raise RuntimeError("the site did not start")
                    time.sleep(0.2)
            yield url
        finally:
            proc.terminate()
            proc.wait(timeout=10)


@pytest.fixture
def page(base_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto(base_url + "/")
        yield page
        context.close()
        browser.close()
