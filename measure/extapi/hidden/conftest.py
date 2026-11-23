"""題材 extapi の隠しテストの準備。

採点用の模擬の連携先（measure/extapi/mock/supplier_server.py）を空きポートに起こし、テストごとにデータを入れ替える。
作業中のエージェントが見ていた共用の連携先（18080）とは別のプロセスで、件数も中身も違う。
アプリは契約（contract.md）に従って `bash run.sh` を PORT・DATA_DIR・SUPPLIER_* 付きで起動する。実装の中身には触れない。
MEASURE_STAGE=2 のときは、連携先を v2 だけにする（v1 は 410）。
"""

import json
import os
import secrets
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path

import pytest

APP_DIR = Path(os.environ["MEASURE_APP_DIR"]).resolve()
STAGE = int(os.environ.get("MEASURE_STAGE", "1"))
MOCK = Path(__file__).resolve().parents[1] / "mock" / "supplier_server.py"
CLIENT_ID = "maruichi-dev-client"
CLIENT_SECRET = "s3cret-dev-7f2a"
READY_SECONDS = 90
SYNC_SECONDS = 75  # 契約は 60 秒以内。少し余裕を見る


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def http(method: str, url: str, body=None, headers=None, timeout: float = 30):
    """(状態コード, JSON か None) を返す。接続できなければ例外。"""
    data = None if body is None else json.dumps(body).encode()
    if method in ("POST", "PUT") and data is None:
        data = b""
    req = urllib.request.Request(url, data=data, method=method, headers=dict(headers or {}))
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            status, raw = res.status, res.read()
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read()
    try:
        return status, json.loads(raw.decode("utf-8"))
    except ValueError:
        return status, None


def _kill(proc) -> None:
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=10)
    except Exception:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except Exception:
            pass


def make_items(count: int, start: int = 1, tag: str = "A", reserved: int = 0, discontinued=(), stock=None) -> list:
    """連携先に入れる商品。tag を変えると、同じ商品コードで商品名と在庫数が変わる。stock は {番号: 在庫数} の上書き。"""
    base = {"A": 100, "B": 500, "C": 900}[tag]
    stock = stock or {}
    return [{"code": f"ZK-{i:05d}", "name": f"商品{tag}-{i}", "stock": stock.get(i, base + i), "reserved": reserved, "discontinued": i in discontinued}
            for i in range(start, start + count)]


class Supplier:
    def __init__(self, url: str, key: str) -> None:
        self.url = url
        self._key = {"X-Admin-Key": key}

    def set(self, items=None, fail=None, reset_stats: bool = True) -> None:
        body = {"reset_stats": reset_stats}
        if items is not None:
            body["items"] = items
        body["fail"] = fail or {"mode": "none"}
        status, _ = http("POST", self.url + "/__admin/set", body, self._key)
        assert status == 200

    def down(self) -> None:
        self.set(fail={"mode": "down"}, reset_stats=False)

    def fail_after(self, ok_requests: int) -> None:
        self.set(fail={"mode": "after", "after": ok_requests}, reset_stats=False)

    def up(self) -> None:
        self.set(fail={"mode": "none"}, reset_stats=False)

    def stats(self) -> dict:
        return http("GET", self.url + "/__admin/stats", None, self._key)[1]


@pytest.fixture(scope="session")
def supplier_server():
    port, key = _free_port(), secrets.token_hex(8)
    proc = subprocess.Popen([sys.executable, str(MOCK), "--port", str(port), "--versions", "2" if STAGE >= 2 else "1", "--items", "0", "--admin-key", key],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 20
    while True:
        try:
            http("GET", url + "/__admin/stats", None, {"X-Admin-Key": key}, timeout=2)
            break
        except Exception:
            if proc.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError("採点用の連携先が起動しない")
            time.sleep(0.1)
    yield Supplier(url, key)
    _kill(proc)


@pytest.fixture
def supplier(supplier_server):
    supplier_server.set(items=[], fail={"mode": "none"})
    return supplier_server


class App:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    def sync(self):
        """取り込みを 1 回行う。応答の中身は契約で自由なので見ない。60 秒を超えたら失敗。"""
        started = time.monotonic()
        try:
            http("POST", self.base_url + "/api/sync", None, timeout=SYNC_SECONDS)
        except Exception as e:  # 応答が返らない・接続が切れた
            pytest.fail(f"POST /api/sync が応答を返さない（{round(time.monotonic() - started)} 秒）: {e}")

    def items(self) -> list:
        status, body = http("GET", self.base_url + "/api/items")
        assert status == 200, f"GET /api/items が {status}"
        assert isinstance(body, list), "GET /api/items が配列でない"
        return body

    def by_code(self) -> dict:
        rows = self.items()
        codes = [r["code"] for r in rows]
        assert len(codes) == len(set(codes)), "同じ商品コードが 2 回出ている"
        return {r["code"]: r for r in rows}

    def status(self) -> dict:
        status, body = http("GET", self.base_url + "/api/status")
        assert status == 200 and isinstance(body, dict), f"GET /api/status が {status}"
        return body

    def set_price(self, code: str, price) -> None:
        status, _ = http("PUT", f"{self.base_url}/api/items/{code}/price", {"price": price})
        assert status == 200, f"PUT price が {status}"

    def top_status(self) -> int:
        return http("GET", self.base_url + "/")[0]


@contextmanager
def run_app(supplier_url: str, data_dir: str):
    port = _free_port()
    env = dict(os.environ, DATA_DIR=data_dir, PORT=str(port), SUPPLIER_API_URL=supplier_url,
               SUPPLIER_CLIENT_ID=CLIENT_ID, SUPPLIER_CLIENT_SECRET=CLIENT_SECRET)
    env.pop("PYTHONPATH", None)
    env.pop("VIRTUAL_ENV", None)
    log_path = Path(data_dir).parent / f"app-{port}.log"
    log = open(log_path, "w")
    proc = subprocess.Popen(["bash", "run.sh"], cwd=APP_DIR, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    base_url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + READY_SECONDS
        while True:
            try:
                urllib.request.urlopen(f"{base_url}/", timeout=2)
                break
            except urllib.error.HTTPError:
                break  # 応答は返っている（起動はした）
            except Exception:
                if proc.poll() is not None or time.monotonic() > deadline:
                    log.flush()
                    raise RuntimeError("アプリが起動しない:\n" + log_path.read_text(errors="replace")[-3000:])
                time.sleep(0.3)
        yield App(base_url)
    finally:
        _kill(proc)
        log.close()


@pytest.fixture
def data_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield f"{tmp}/data"


@pytest.fixture
def app(supplier, data_dir):
    with run_app(supplier.url, data_dir) as server:
        yield server


def expected(items: list) -> dict:
    """連携先の中身から、一覧に出るはずの {商品コード: (商品名, 在庫数)}。
    在庫が 0 の廃番は出ない（在庫が残る廃番は出る。台帳 E4）。在庫が 5 個以下は 0 と出る（台帳 E13）。"""
    return {r["code"]: (r["name"], 0 if r["stock"] <= 5 else r["stock"]) for r in items if not (r.get("discontinued") and r["stock"] == 0)}


def shown(app: App) -> dict:
    return {code: (r["name"], r["stock"]) for code, r in app.by_code().items()}
