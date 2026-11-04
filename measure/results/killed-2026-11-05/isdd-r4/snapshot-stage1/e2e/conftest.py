"""E2E テストの共通設定。Chromium を 1 回だけ起動し、テストごとに一時のデータと Web アプリを用意する。"""

import pytest
from playwright.sync_api import sync_playwright

from e2e.support import start_app_server


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def make_server(tmp_path):
    """テスト用の Web アプリを起動する関数を返す。テスト終了時に停止する。"""
    servers = []

    def _make(idle_timeout=1800):
        server = start_app_server(tmp_path / f"data{len(servers)}", idle_timeout)
        servers.append(server)
        return server

    yield _make
    for server in servers:
        server.stop()


@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()
