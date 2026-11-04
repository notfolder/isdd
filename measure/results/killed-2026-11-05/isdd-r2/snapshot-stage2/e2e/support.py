"""E2E テストの共通部分。アプリを別プロセスで起動し、Chromium で画面を操作する。"""

import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

from src import accounts, db, equipment, lending

ROOT = Path(__file__).resolve().parent.parent


def free_port():
    """空いている TCP ポートを 1 つ返す。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def new_data_dir():
    """空の DATA_DIR（一時ディレクトリ）を作り、スキーマを作って返す。"""
    data_dir = Path(tempfile.mkdtemp(prefix="ledger-e2e-"))
    conn = db.connect(data_dir)
    db.init_schema(conn)
    conn.close()
    return data_dir


def seed_accounts(data_dir, rows):
    """アカウントを登録する。rows は (社員番号, 名前, パスワード) のリスト。最初の 1 件が担当者になる。"""
    conn = db.connect(data_dir)
    try:
        for employee_number, name, password in rows:
            accounts.register_account(conn, employee_number, name, password)
    finally:
        conn.close()


def seed_equipment(data_dir, rows):
    """備品を登録する。rows は (管理番号, 備品名) のリスト。"""
    conn = db.connect(data_dir)
    try:
        for number, name in rows:
            equipment.create_equipment(conn, number, name)
    finally:
        conn.close()


def seed_lending(data_dir, rows):
    """貸出を記録する。rows は (管理番号, 社員番号, 貸出日) のリスト。"""
    conn = db.connect(data_dir)
    try:
        for number, employee_number, lent_on in rows:
            lending.lend_equipment(conn, number, employee_number, lent_on)
    finally:
        conn.close()


def start_server(data_dir, port, idle_timeout_seconds=1800):
    """アプリを別プロセスで起動し、応答できるまで待つ。戻り値は Popen。"""
    env = {
        "PORT": str(port),
        "DATA_DIR": str(data_dir),
        "SESSION_IDLE_TIMEOUT_SECONDS": str(idle_timeout_seconds),
        "PATH": "/usr/bin:/bin",
    }
    with open(Path(data_dir) / "server.log", "w") as log:
        proc = subprocess.Popen(
            [sys.executable, "-m", "src.main"], cwd=ROOT, env=env, stdout=log, stderr=log
        )
    base = f"http://127.0.0.1:{port}/"
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            urllib.request.urlopen(base, timeout=2).read()
            return proc
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.2)
    proc.kill()
    raise RuntimeError("アプリが起動しませんでした")


class LedgerE2ECase(unittest.TestCase):
    """1 テストごとに、新しい DB とアプリのプロセスと Chromium を用意する基底クラス。"""

    idle_timeout_seconds = 1800

    def setUp(self):
        self.data_dir = new_data_dir()
        self.port = free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        self.prepare_data()
        self.proc = start_server(self.data_dir, self.port, self.idle_timeout_seconds)
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch()
        self.page = self.browser.new_page()

    def prepare_data(self):
        """テストの前提データを作る。下位クラスで上書きする。"""

    def tearDown(self):
        self.browser.close()
        self.playwright.stop()
        self.proc.terminate()
        self.proc.wait(timeout=10)

    def open(self, path):
        """パスを開く。"""
        self.page.goto(self.base + path)

    def login(self, employee_number, password):
        """ログイン画面から入り、トップへ戻るまで待つ。"""
        self.open("/login/")
        self.page.fill("#id_employee_number", employee_number)
        self.page.fill("#id_password", password)
        self.page.get_by_role("button", name="ログイン").click()
        self.page.wait_for_url(self.base + "/")

    def register(self, employee_number, name, password):
        """アカウント登録画面から登録し、ログイン画面へ移るまで待つ。"""
        self.open("/accounts/register/")
        self.page.fill("#id_employee_number", employee_number)
        self.page.fill("#id_name", name)
        self.page.fill("#id_password", password)
        self.page.get_by_role("button", name="登録").click()
        self.page.wait_for_url("**/login/**")

    def row(self, number):
        """管理番号の行を返す。"""
        return self.page.locator(f'tbody tr[data-equipment-number="{number}"]')
