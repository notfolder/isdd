"""E2E テストの共通の準備。テストごとに空のデータで run.sh を起動し、終了時に起動したプロセスだけを止める。"""
import os
import pathlib
import socket
import subprocess
import time
import urllib.request

import pytest
from playwright.sync_api import expect, sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def app_url(tmp_path):
    """空の DATA_DIR で run.sh を起動し、ベースの URL を返す。終了時は起動した PID だけを止める。"""
    port = _free_port()
    log_path = tmp_path / "server.log"
    env = dict(os.environ, PORT=str(port), DATA_DIR=str(tmp_path / "data"))
    with open(log_path, "w", encoding="utf-8") as log:
        process = subprocess.Popen(["bash", "run.sh"], cwd=ROOT, env=env, stdout=log, stderr=log)
    base = f"http://localhost:{port}"
    try:
        deadline = time.time() + 60
        while True:
            if process.poll() is not None:
                raise RuntimeError("run.sh が終了しました: " + log_path.read_text(encoding="utf-8"))
            try:
                with urllib.request.urlopen(base + "/", timeout=2) as response:
                    if response.status == 200:
                        break
            except OSError:
                pass
            if time.time() > deadline:
                raise RuntimeError("起動の待ち時間を超えました")
            time.sleep(0.3)
        yield base
    finally:
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


@pytest.fixture
def page(app_url):
    """Chromium のページを 1 つ開く。"""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(base_url=app_url)
        page = context.new_page()
        page.set_default_timeout(10000)
        yield page
        context.close()
        browser.close()


class UI:
    """画面操作の補助。入力欄は isdd の契約どおり id で指定する。"""

    def __init__(self, page):
        self.page = page

    def register(self, number, name, password):
        self.page.goto("/accounts/register/")
        self.page.fill("#id_employee_number", number)
        self.page.fill("#id_name", name)
        self.page.fill("#id_password", password)
        self.page.get_by_role("button", name="登録").click()

    def login(self, number, password):
        self.page.goto("/login/")
        self.page.fill("#id_employee_number", number)
        self.page.fill("#id_password", password)
        self.page.get_by_role("button", name="ログイン").click()

    def logout(self):
        self.page.get_by_role("button", name="ログアウト").click()

    def register_equipment(self, number, name):
        self.page.goto("/equipment/new/")
        self.page.fill("#id_equipment_number", number)
        self.page.fill("#id_name", name)
        self.page.get_by_role("button", name="保存").click()


@pytest.fixture
def ui(page):
    """画面操作の補助を返す。"""
    return UI(page)


@pytest.fixture
def expect_(page):
    """Playwright の expect を返す。"""
    return expect
