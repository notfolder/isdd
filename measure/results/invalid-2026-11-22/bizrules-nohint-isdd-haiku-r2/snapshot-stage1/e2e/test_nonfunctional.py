"""非機能要件の E2E。"""

import socket
import sqlite3
import time
import urllib.request

from playwright.sync_api import expect

from helpers import register


def _seed(data_dir, users: int, equipment: int, lendings: int) -> None:
    """前処理として DB に直接データを入れる（備品 500 件、利用者 50 人の規模を作るため）。"""
    conn = sqlite3.connect(data_dir / "app.db")
    try:
        conn.executemany(
            "INSERT INTO users (employee_number, name, password_hash, role, created_at)"
            " VALUES (?, ?, 'x', 'member', '2026-11-22T00:00:00+09:00')",
            [(f"{200000 + i}", f"利用者{i}") for i in range(1, users + 1)])
        conn.executemany("INSERT INTO equipment (equipment_number, name) VALUES (?, ?)",
                         [(f"EQ-{i:04d}", f"備品{i}") for i in range(1, equipment + 1)])
        conn.executemany("INSERT INTO lendings (equipment_id, user_id, lent_on) VALUES (?, ?, '2026-11-20')",
                         [(i, 2 + (i % users), ) for i in range(1, lendings + 1)])
        conn.commit()
    finally:
        conn.close()


def test_status_response_time(server, page):
    """備品 500 件、利用者 50 人で、貸出状況の全行が 2 秒以内に表示される。"""
    register(page, server, "100001", "山田 太郎")
    _seed(server.data_dir, users=50, equipment=500, lendings=100)
    start = time.perf_counter()
    page.goto(server.url("/"))
    expect(page.locator("tbody tr")).to_have_count(500)
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0, f"貸出状況の表示に {elapsed:.2f} 秒かかりました"


def test_password_not_stored_plain(server, page):
    """登録したパスワードの文字列は、DB ファイルのどこにも無い。"""
    password = "plain-check-pass-9"
    register(page, server, "100001", "山田 太郎", password=password)
    raw = (server.data_dir / "app.db").read_bytes()
    assert password.encode("utf-8") not in raw


def _local_addresses() -> list[str]:
    addresses = ["127.0.0.1"]
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.connect(("10.255.255.255", 1))
            ip = sock.getsockname()[0]
            if ip not in addresses:
                addresses.append(ip)
        except OSError:
            pass
    return addresses


def test_internal_access_reachable(server):
    """サーバーは全インターフェースで待ち受け、ループバックと機の別の IP（取れる場合）から開ける。"""
    for host in _local_addresses():
        with urllib.request.urlopen(f"http://{host}:{server.port}/", timeout=5) as response:
            assert response.status == 200
