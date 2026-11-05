"""E2E テスト: 実サーバー（src/server.py を子プロセスで起動）に HTTP で問い合わせて、画面と API を確かめる。

各テストは一時 DATA_DIR を使う。起動したサーバーは、このテストが起動した子プロセスだけを終了させる。
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_SCRIPT = os.path.join(PROJECT_ROOT, "src", "server.py")
NAME_ERROR = "Please enter a name of 1 to 20 characters."


def free_port():
    """使われていないローカルのポート番号を 1 つ返す。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class ServerProcess:
    """src/server.py を子プロセスとして起動し、終了させる。"""

    def __init__(self, data_dir, log_path):
        self.data_dir = data_dir
        self.log_path = log_path
        self.port = None
        self.proc = None

    def start(self):
        self.port = free_port()
        env = dict(os.environ, PORT=str(self.port), DATA_DIR=self.data_dir)
        with open(self.log_path, "a", encoding="utf-8") as log:
            self.proc = subprocess.Popen(
                [sys.executable, SERVER_SCRIPT], env=env, stdout=log, stderr=log
            )
        deadline = time.time() + 15
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError("the server exited early; see " + self.log_path)
            try:
                with socket.create_connection(("127.0.0.1", self.port), timeout=0.2):
                    return
            except OSError:
                time.sleep(0.05)
        raise RuntimeError("the server did not start listening in time")

    def stop(self):
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=5)
        self.proc = None

    def url(self, path):
        return "http://127.0.0.1:%d%s" % (self.port, path)


def http(url, method="GET", payload=None):
    """(状態コード, 本文) を返す。エラー状態でも例外にしない。"""
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8")


class WheelE2ETest(unittest.TestCase):
    """景品ルーレットの利用シナリオを、実サーバーに対して確かめる。"""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="wheel-e2e-")
        cls.server = ServerProcess(os.path.join(cls.tmp, "data"), os.path.join(cls.tmp, "server.log"))
        cls.server.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def get_json(self, path):
        status, body = http(self.server.url(path))
        self.assertEqual(status, 200, body)
        return json.loads(body)

    def records_of(self, name):
        return self.get_json("/api/records?player_name=" + name.replace(" ", "%20"))

    def test_spin_and_record(self):
        name = "Tester A"
        prizes = self.get_json("/api/prizes")
        before = len(self.records_of(name))
        wins = 0
        for _ in range(20):
            status, body = http(self.server.url("/api/spin"), "POST", {"player_name": name})
            self.assertEqual(status, 200, body)
            outcome = json.loads(body)
            chosen = prizes[outcome["segment_index"]]
            self.assertEqual(chosen["id"], outcome["prize_id"])
            self.assertEqual(chosen["is_miss"], outcome["is_miss"])
            if outcome["is_miss"]:
                self.assertIsNone(outcome["record_id"])
            else:
                self.assertIsNotNone(outcome["record_id"])
                wins += 1
        self.assertEqual(len(self.records_of(name)) - before, wins)

    def test_name_validation(self):
        name = "Tester V"
        before = len(self.records_of(name))
        for raw in ["", "   ", "x" * 21]:
            with self.subTest(raw=raw):
                status, body = http(self.server.url("/api/spin"), "POST", {"player_name": raw})
                self.assertEqual(status, 400)
                self.assertEqual(json.loads(body)["error"], NAME_ERROR)
        self.assertEqual(len(self.records_of(name)), before)
        status, _ = http(self.server.url("/api/spin"), "POST", {"player_name": "x" * 20})
        self.assertEqual(status, 200)

    def test_view_prizes(self):
        prizes = self.get_json("/api/prizes")
        self.assertEqual(len(prizes), 7)
        self.assertAlmostEqual(sum(p["probability_percent"] for p in prizes), 100.0, places=1)
        self.assertEqual(sum(1 for p in prizes if p["is_miss"]), 1)
        status, body = http(self.server.url("/prizes"))
        self.assertEqual(status, 200)
        self.assertIn("Prize List", body)
        self.assertIn('id="prize-rows"', body)

    def test_view_own_records(self):
        records = self.records_of("Sample Player")
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["won_at"], "2026-11-05 09:15:00")
        self.assertEqual(records[1]["won_at"], "2026-11-04 18:30:00")
        self.assertEqual(self.records_of("Nobody Here"), [])
        status, body = http(self.server.url("/api/records?player_name=%20%20"))
        self.assertEqual(status, 400)
        self.assertEqual(json.loads(body)["error"], NAME_ERROR)

    def test_navigation(self):
        for path in ["/", "/prizes", "/records"]:
            with self.subTest(path=path):
                status, body = http(self.server.url(path))
                self.assertEqual(status, 200)
                self.assertIn('lang="en"', body)
                self.assertIn('href="/"', body)
                self.assertIn('href="/prizes"', body)
                self.assertIn('href="/records"', body)
                self.assertIn("Spin Wheel", body)
                self.assertIn("Prize List", body)
                self.assertIn("My Winning Records", body)
        status, css = http(self.server.url("/static/styles.css"))
        self.assertEqual(status, 200)
        self.assertIn("#d3d3d3", css.lower())
        self.assertIn("#8b0000", css.lower())
        status, _ = http(self.server.url("/static/js/wheel.js"))
        self.assertEqual(status, 200)
        status, _ = http(self.server.url("/no-such-page"))
        self.assertEqual(status, 404)

    def test_seed_data(self):
        data_dir = os.path.join(self.tmp, "seed-data")
        server = ServerProcess(data_dir, os.path.join(self.tmp, "seed-server.log"))
        try:
            server.start()
            prizes = json.loads(http(server.url("/api/prizes"))[1])
            records = json.loads(http(server.url("/api/records?player_name=Sample%20Player"))[1])
            self.assertEqual(len(prizes), 7)
            self.assertEqual(len(records), 2)
        finally:
            server.stop()
        server = ServerProcess(data_dir, os.path.join(self.tmp, "seed-server.log"))
        try:
            server.start()
            prizes = json.loads(http(server.url("/api/prizes"))[1])
            records = json.loads(http(server.url("/api/records?player_name=Sample%20Player"))[1])
            self.assertEqual(len(prizes), 7)
            self.assertEqual(len(records), 2)
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
