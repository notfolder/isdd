"""題材 needfit の隠しテストの準備。契約（contracts/stage1.md）に従って、テストごとに空のデータでアプリを起動し、JSON の API を呼ぶ。標準ライブラリだけを使う。"""

import json
import os
import signal
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

APP_DIR = Path(os.environ["MEASURE_APP_DIR"]).resolve()
READY_SECONDS = 90


class Api:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    def call(self, method: str, path: str, body=None, raw: bytes = None, content_type: str = "application/json"):
        """(ステータス, 本文のバイト列, Content-Type) を返す。4xx・5xx も例外にしない。"""
        data = raw if raw is not None else (json.dumps(body).encode("utf-8") if body is not None else None)
        req = urllib.request.Request(self.base_url + path, data=data, method=method)
        if data is not None:
            req.add_header("Content-Type", content_type)
        try:
            with urllib.request.urlopen(req, timeout=20) as res:
                return res.status, res.read(), res.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            return e.code, e.read(), e.headers.get("Content-Type", "")

    def json(self, method: str, path: str, body=None):
        status, raw, _ = self.call(method, path, body)
        try:
            return status, json.loads(raw.decode("utf-8")) if raw else None
        except ValueError:
            return status, None

    def add(self, code: str, **over) -> int:
        item = {"code": code, "name": f"品目 {code}", "stock": 100, "daily_usage": 1, "lead_days": 1, "on_order": 0,
                "min_order_qty": 1, "supplier": "山田商会", "unit_price": 100, "location": "A-1"}
        item.update(over)
        return self.json("POST", "/api/items", item)[0]

    def items(self) -> dict:
        status, data = self.json("GET", "/api/items")
        assert status == 200 and isinstance(data, list), f"GET /api/items が一覧を返さない: {status}"
        return {i["code"]: i for i in data}

    def reorder(self, code: str) -> bool:
        flag = self.items()[code].get("reorder")
        assert isinstance(flag, bool), f"reorder が true / false でない: {flag!r}"
        return flag


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def api():
    with tempfile.TemporaryDirectory() as tmp:
        port = _free_port()
        env = dict(os.environ, DATA_DIR=f"{tmp}/data", PORT=str(port))
        env.pop("PYTHONPATH", None)
        env.pop("VIRTUAL_ENV", None)
        log_path = Path(tmp) / "app.log"
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
                    break  # 応答はしている。GET / が 200 かどうかは、テストで見る
                except Exception:
                    if proc.poll() is not None or time.monotonic() > deadline:
                        log.flush()
                        raise RuntimeError("アプリが起動しない:\n" + log_path.read_text(errors="replace")[-3000:])
                    time.sleep(0.2)
            yield Api(base_url)
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
