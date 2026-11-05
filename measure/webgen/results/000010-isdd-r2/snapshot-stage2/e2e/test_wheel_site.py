"""E2E テスト: 実サーバー（python3 -m app の子プロセス）に HTTP で要求し、詳細設計書 8-2 のシナリオを確かめる。

テストごとに、空いているポートと一時 DATA_DIR で起動する。終了時は自分が起動した子プロセスだけを止める。
"""

import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PRIZE_COUNT = 6
SAMPLE_RECORD_COUNT = 3
START_TIMEOUT_SECONDS = 15


def _free_port() -> int:
    """127.0.0.1 の空いているポート番号を返す。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class ServerProcess:
    """実サーバーを子プロセスとして起動・停止する。"""

    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir
        self.port = _free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        self._proc: Optional[subprocess.Popen] = None

    def start(self) -> None:
        env = dict(os.environ)
        env["PORT"] = str(self.port)
        env["DATA_DIR"] = self.data_dir
        self._proc = subprocess.Popen(
            [sys.executable, "-m", "app"],
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + START_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if self._proc.poll() is not None:
                _, err = self._proc.communicate()
                raise RuntimeError("server exited during start: " + err.decode("utf-8", "replace"))
            try:
                status, _, _ = request("GET", self.base + "/")
                if status == 200:
                    return
            except OSError:
                pass
            time.sleep(0.1)
        self.stop()
        raise RuntimeError("server did not start in time")

    def stop(self) -> None:
        if self._proc is None or self._proc.poll() is not None:
            self._proc = None
            return
        self._proc.terminate()
        try:
            self._proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._proc.kill()
            self._proc.wait(timeout=5)
        self._proc = None


def request(method: str, url: str, body: Optional[Dict[str, Any]] = None) -> Tuple[int, str, str]:
    """HTTP 要求を送り、(状態番号, Content-Type, 本文) を返す。エラーの応答も返す。"""
    data = None
    headers = {"Accept": "*/*"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.headers.get("Content-Type", ""), resp.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        return error.code, error.headers.get("Content-Type", ""), error.read().decode("utf-8")


def get_json(url: str) -> Tuple[int, Any]:
    status, _, text = request("GET", url)
    return status, json.loads(text)


def post_json(url: str, body: Any) -> Tuple[int, Any]:
    status, _, text = request("POST", url, body)
    return status, json.loads(text)


def winnings_of(base: str, name: str) -> List[Dict[str, Any]]:
    query = urllib.parse.urlencode({"name": name})
    status, payload = get_json(f"{base}/api/winnings?{query}")
    if status != 200:
        raise AssertionError(f"winnings request failed: {status} {payload}")
    return payload["winnings"]


class WheelSiteTest(unittest.TestCase):
    """詳細設計書 8-2 のシナリオ。サーバーはクラスで 1 つ共有し、名前はテストごとに一意にする。"""

    server: ServerProcess
    _data_dir: tempfile.TemporaryDirectory

    @classmethod
    def setUpClass(cls) -> None:
        cls._data_dir = tempfile.TemporaryDirectory()
        cls.server = ServerProcess(cls._data_dir.name)
        cls.server.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.stop()
        cls._data_dir.cleanup()

    def unique_name(self, prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:8]}"

    def test_spin_and_record(self) -> None:
        base = self.server.base
        name = self.unique_name("Alice")

        status, _, page = request("GET", base + "/")
        self.assertEqual(status, 200)
        self.assertIn('id="spin-form"', page)

        status, spin = post_json(base + "/api/spins", {"player_name": f"  {name}  "})
        self.assertEqual(status, 200)
        self.assertEqual(spin["record"]["player_name"], name)
        self.assertEqual(spin["prize"]["name"], spin["record"]["prize_name"])
        self.assertTrue(spin["prize"]["description"])
        self.assertTrue(0 <= spin["prize_index"] < spin["prize_count"])

        records = winnings_of(base, name)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["prize_name"], spin["prize"]["name"])

    def test_spin_requires_valid_name(self) -> None:
        base = self.server.base
        before = len(winnings_of(base, "Sample Player"))

        status, payload = post_json(base + "/api/spins", {"player_name": "   "})
        self.assertEqual(status, 400)
        self.assertIn("Please enter your name", payload["error"])

        too_long = "x" * 31
        status, payload = post_json(base + "/api/spins", {"player_name": too_long})
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "Name must be 30 characters or fewer.")

        status, payload = get_json(base + "/api/winnings?" + urllib.parse.urlencode({"name": too_long}))
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "Name must be 30 characters or fewer.")

        self.assertEqual(len(winnings_of(base, "Sample Player")), before)

    def test_prize_list_shows_all_prizes(self) -> None:
        base = self.server.base
        status, payload = get_json(base + "/api/prizes")
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["prizes"]), SAMPLE_PRIZE_COUNT)
        for prize in payload["prizes"]:
            self.assertTrue(prize["name"])
            self.assertIn("description", prize)

        status, _, page = request("GET", base + "/prizes")
        self.assertEqual(status, 200)
        self.assertIn('id="prize-list"', page)
        self.assertIn("/static/prizes.js", page)

    def test_own_winnings_filtered_and_newest_first(self) -> None:
        base = self.server.base
        bob = self.unique_name("Bob")
        nobody = self.unique_name("Nobody")
        first = post_json(base + "/api/spins", {"player_name": bob})[1]["record"]
        second = post_json(base + "/api/spins", {"player_name": bob})[1]["record"]

        mine = winnings_of(base, bob)
        self.assertEqual([row["id"] for row in mine], [second["id"], first["id"]])
        self.assertGreaterEqual(mine[0]["won_at"], mine[1]["won_at"])

        sample = winnings_of(base, "sample player")
        self.assertEqual(len(sample), SAMPLE_RECORD_COUNT)
        self.assertTrue(all(row["id"] not in {first["id"], second["id"]} for row in sample))

        self.assertEqual(winnings_of(base, nobody), [])

    def test_every_prize_is_drawn(self) -> None:
        base = self.server.base
        name = self.unique_name("Odds")
        status, prizes = get_json(base + "/api/prizes")
        self.assertEqual(status, 200)
        expected = {prize["id"] for prize in prizes["prizes"]}

        seen = set()
        for _ in range(300):
            status, spin = post_json(base + "/api/spins", {"player_name": name})
            self.assertEqual(status, 200)
            seen.add(spin["prize"]["id"])
        self.assertEqual(seen, expected)

    def test_navigation_links_on_every_page(self) -> None:
        base = self.server.base
        pages = {"/": "/", "/prizes": "/prizes", "/my-winnings": "/my-winnings"}
        for path, current in pages.items():
            with self.subTest(page=path):
                status, _, html = request("GET", base + path)
                self.assertEqual(status, 200)
                for href in ["/", "/prizes", "/my-winnings"]:
                    self.assertIn(f'href="{href}"', html)
                marked = re.findall(r'<a href="([^"]+)" aria-current="page">', html)
                self.assertEqual(marked, [current])

    def test_theme_ivory_and_dark_green(self) -> None:
        base = self.server.base
        for path in ["/", "/prizes", "/my-winnings"]:
            with self.subTest(page=path):
                status, _, html = request("GET", base + path)
                self.assertEqual(status, 200)
                self.assertIn("/static/style.css", html)

        status, content_type, css = request("GET", base + "/static/style.css")
        self.assertEqual(status, 200)
        self.assertIn("text/css", content_type)
        self.assertIn("#FFFFF0", css)
        self.assertIn("#006400", css)

        for asset in ["/static/style.css", "/static/spin.js", "/static/common.js",
                      "/static/my-winnings.js", "/static/prizes.js"]:
            with self.subTest(asset=asset):
                status, _, text = request("GET", base + asset)
                self.assertEqual(status, 200)
                self.assertNotIn("#D3D3D3", text.upper())
                self.assertNotIn("#8B0000", text.upper())
                self.assertNotIn("A52A2A", text.upper())

    def test_spin_name_field_is_required_next_to_spin(self) -> None:
        base = self.server.base
        status, _, page = request("GET", base + "/")
        self.assertEqual(status, 200)

        start = page.index('<form id="spin-form"')
        end = page.index("</form>", start)
        form = page[start:end]
        self.assertIn('id="spin-button"', form)
        self.assertRegex(form, r'<input[^>]*id="player-name"[^>]*\srequired[\s>]')
        self.assertIn("Your name (required)", form)

        before = len(winnings_of(base, "Sample Player"))
        status, payload = post_json(base + "/api/spins", {"player_name": ""})
        self.assertEqual(status, 400)
        self.assertIn("Please enter your name", payload["error"])
        self.assertEqual(len(winnings_of(base, "Sample Player")), before)

    def test_record_shows_name_prize_and_date(self) -> None:
        base = self.server.base
        name = self.unique_name("Alice")
        status, spin = post_json(base + "/api/spins", {"player_name": name})
        self.assertEqual(status, 200)
        record = spin["record"]
        self.assertEqual(record["player_name"], name)
        self.assertEqual(record["prize_name"], spin["prize"]["name"])
        self.assertTrue(record["won_at"].endswith("Z"))

        rows = winnings_of(base, name)
        self.assertEqual(len(rows), 1)
        for key in ["player_name", "prize_name", "won_at"]:
            self.assertIn(key, rows[0])
        self.assertEqual(rows[0]["player_name"], name)

        status, _, page = request("GET", base + "/my-winnings")
        self.assertEqual(status, 200)
        self.assertIn('<th scope="col">Player</th><th scope="col">Prize</th><th scope="col">Date won</th>', page)

        status, _, script = request("GET", base + "/static/spin.js")
        self.assertEqual(status, 200)
        self.assertIn('"Date won"', script)
        self.assertIn('"Player"', script)

    def test_empty_data_dir_gets_samples(self) -> None:
        with tempfile.TemporaryDirectory() as fresh:
            data_dir = os.path.join(fresh, "new-data")
            server = ServerProcess(data_dir)
            server.start()
            try:
                status, payload = get_json(server.base + "/api/prizes")
                self.assertEqual(status, 200)
                self.assertEqual(len(payload["prizes"]), SAMPLE_PRIZE_COUNT)
                self.assertEqual(len(winnings_of(server.base, "Sample Player")), SAMPLE_RECORD_COUNT)
            finally:
                server.stop()

            again = ServerProcess(data_dir)
            again.start()
            try:
                status, payload = get_json(again.base + "/api/prizes")
                self.assertEqual(len(payload["prizes"]), SAMPLE_PRIZE_COUNT)
                self.assertEqual(len(winnings_of(again.base, "Sample Player")), SAMPLE_RECORD_COUNT)
            finally:
                again.stop()


if __name__ == "__main__":
    unittest.main()
