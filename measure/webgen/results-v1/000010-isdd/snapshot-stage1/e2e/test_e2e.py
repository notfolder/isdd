"""E2E テスト。実サーバーを一時 DATA_DIR と空きポートで起動し、HTTP で確かめる。

各テスト関数は 1 つの E2E シナリオに対応する（対応表で結ぶ）。
"""

import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Server:
    """python3 -m app を一時 DATA_DIR で起動する。終了時は自分の PID だけを止める。"""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.port = _free_port()
        env = dict(os.environ, PORT=str(self.port), DATA_DIR=data_dir)
        self.process = subprocess.Popen(
            [sys.executable, "-m", "app"], cwd=PROJECT_ROOT, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        self.base = f"http://127.0.0.1:{self.port}"
        self._wait_ready()

    def _wait_ready(self):
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                urllib.request.urlopen(self.base + "/", timeout=1).read()
                return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("server did not start")

    def stop(self):
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()

    def request(self, method, path, payload=None):
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status, response.read(), response.headers.get("Content-Type", "")
        except urllib.error.HTTPError as error:
            return error.code, error.read(), error.headers.get("Content-Type", "")

    def json(self, method, path, payload=None):
        status, body, _ = self.request(method, path, payload)
        return status, json.loads(body)

    def db_path(self):
        return os.path.join(self.data_dir, "wheel.sqlite3")


class ScenarioCase(unittest.TestCase):
    """各テストに新しい空の DATA_DIR のサーバーを 1 つ用意する。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.server = Server(os.path.join(self._tmp.name, "data"))

    def tearDown(self):
        self.server.stop()
        self._tmp.cleanup()


class E2EScenarios(ScenarioCase):
    def test_spin_and_record(self):
        status, body = self.server.json("POST", "/api/spin", {"player_name": "Alice"})
        self.assertEqual(status, 200)
        _, prizes = self.server.json("GET", "/api/prizes")
        self.assertIn(body["prize"]["name"], [p["name"] for p in prizes["prizes"]])
        status, records = self.server.json("GET", "/api/records?player_name=Alice")
        self.assertEqual(status, 200)
        self.assertEqual(len(records["records"]), 1)
        self.assertEqual(records["records"][0]["prize_name"], body["prize"]["name"])
        self.assertTrue(records["records"][0]["spun_at"])

    def test_validate_player_name(self):
        for payload in [{"player_name": ""}, {"player_name": "   "}, {"player_name": "a" * 31}]:
            status, body = self.server.json("POST", "/api/spin", payload)
            self.assertEqual(status, 400)
            self.assertIn("error", body)
        status, body = self.server.json("GET", "/api/records?player_name=")
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "Please enter your name")
        status, _ = self.server.json("GET", "/api/records?player_name=" + "a" * 31)
        self.assertEqual(status, 400)
        with sqlite3.connect(self.server.db_path()) as connection:
            count = connection.execute("SELECT COUNT(*) FROM spin_record").fetchone()[0]
        self.assertEqual(count, 0)

    def test_view_prize_list(self):
        status, body = self.server.json("GET", "/api/prizes")
        self.assertEqual(status, 200)
        self.assertEqual(len(body["prizes"]), 6)
        for prize in body["prizes"]:
            self.assertTrue(prize["name"])
            self.assertIn("description", prize)
        status, body_bytes, content_type = self.server.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b'id="view-prizes"', body_bytes)
        self.assertIn("text/html", content_type)

    def test_view_own_records(self):
        self.server.json("POST", "/api/spin", {"player_name": "Alice"})
        self.server.json("POST", "/api/spin", {"player_name": "Alice"})
        self.server.json("POST", "/api/spin", {"player_name": "Bob"})
        status, body = self.server.json("GET", "/api/records?player_name=Alice")
        self.assertEqual(status, 200)
        self.assertEqual(len(body["records"]), 2)
        times = [r["spun_at"] for r in body["records"]]
        self.assertEqual(times, sorted(times, reverse=True))
        status, body = self.server.json("GET", "/api/records?player_name=Carol")
        self.assertEqual(status, 200)
        self.assertEqual(body["records"], [])

    def test_navigate_menu(self):
        status, body_bytes, _ = self.server.request("GET", "/")
        self.assertEqual(status, 200)
        html = body_bytes.decode("utf-8")
        for href, label in [("#/spin", "Spin"), ("#/prizes", "Prizes"), ("#/records", "My Records")]:
            self.assertIn(f'href="{href}"', html)
            self.assertIn(f">{label}</a>", html)

    def test_empty_prizes(self):
        with sqlite3.connect(self.server.db_path()) as connection:
            with connection:
                connection.execute("DELETE FROM prize")
        status, body = self.server.json("POST", "/api/spin", {"player_name": "Alice"})
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "No prizes are available")
        status, body = self.server.json("GET", "/api/prizes")
        self.assertEqual(status, 200)
        self.assertEqual(body["prizes"], [])
        status, records = self.server.json("GET", "/api/records?player_name=Alice")
        self.assertEqual(records["records"], [])

    def test_first_start_and_theme(self):
        env = dict(os.environ, PORT=str(_free_port()), DATA_DIR=os.path.join(self.server.data_dir, "fresh"))
        setup = subprocess.run(["bash", "setup.sh"], cwd=PROJECT_ROOT, capture_output=True, text=True)
        self.assertEqual(setup.returncode, 0, setup.stderr)
        run = subprocess.Popen(["bash", "run.sh"], cwd=PROJECT_ROOT, env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            base = f"http://127.0.0.1:{env['PORT']}"
            deadline = time.time() + 10
            while True:
                try:
                    urllib.request.urlopen(base + "/", timeout=1).read()
                    break
                except OSError:
                    if time.time() > deadline:
                        raise
                    time.sleep(0.1)
            with urllib.request.urlopen(base + "/api/prizes", timeout=5) as response:
                prizes = json.loads(response.read())["prizes"]
            self.assertEqual(len(prizes), 6)
            with urllib.request.urlopen(base + "/style.css", timeout=5) as response:
                css = response.read().decode("utf-8")
            self.assertIn("#e6e6e6", css)
            self.assertIn("#8b0000", css)
            with urllib.request.urlopen(base + "/", timeout=5) as response:
                html = response.read().decode("utf-8")
            self.assertIn('lang="en"', html)
            self.assertIn("Spin the wheel", html)
        finally:
            run.terminate()
            run.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
