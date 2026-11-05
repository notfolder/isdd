"""End-to-end scenarios (design 8-2). Each test starts the real HTTP server on a
free port with a temporary DATA_DIR and talks to it over HTTP like a browser would."""

import concurrent.futures
import http.cookiejar
import json
import os
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))

from server import build_server  # noqa: E402


def _client(base):
    """Return an opener with its own cookie jar, i.e. one browser."""
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar)), base


def _get(client, path):
    opener, base = client
    with opener.open(base + path, timeout=10) as res:
        return res.status, res.read().decode("utf-8")


def _post_json(client, path, body):
    opener, base = client
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(base + path, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with opener.open(req, timeout=10) as res:
            return res.status, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read().decode("utf-8"))


def _spin_until(client, want_recorded, attempts=300):
    """Spin until a result with recorded == want_recorded appears."""
    for _ in range(attempts):
        status, payload = _post_json(client, "/api/spin", {"display_name": "Tester"})
        assert status == 200, payload
        if payload["recorded"] == want_recorded:
            return payload
    raise AssertionError("no matching spin result in %d attempts" % attempts)


class WheelScenarios(unittest.TestCase):
    """One test method per E2E scenario DS-TS-* (name: test_<scenario in lower_snake>)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.httpd = build_server(0, self._tmp.name)
        port = self.httpd.server_address[1]
        self.base = "http://127.0.0.1:%d" % port
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self._tmp.cleanup()

    def new_client(self):
        return _client(self.base)

    # DS-TS-EMPTY-DATA-START
    def test_empty_data_start(self):
        client = self.new_client()
        status, body = _get(client, "/api/prizes")
        prizes = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(len(prizes), 8)
        self.assertEqual(sum(p["weight"] for p in prizes), 100)
        status, html = _get(client, "/")
        self.assertEqual(status, 200)
        self.assertIn("Wheel of Fortune", html)

    # DS-TS-SPIN-AND-RECORD
    def test_spin_and_record(self):
        client = self.new_client()
        result = _spin_until(client, want_recorded=True)
        self.assertIn(result["prize"]["name"], [p["name"] for p in json.loads(_get(client, "/api/prizes")[1]) if p["is_win"]])
        _, body = _get(client, "/api/winnings")
        records = json.loads(body)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["prize_name"], result["prize"]["name"])

    # DS-TS-BROWSE-PRIZES
    def test_browse_prizes(self):
        client = self.new_client()
        _, body = _get(client, "/api/prizes")
        prizes = json.loads(body)
        names = [p["name"] for p in prizes]
        self.assertIn("Free Coffee", names)
        self.assertIn("Better Luck Next Time", names)
        # Chances are weight / total; the display sums to 100%.
        total = sum(p["weight"] for p in prizes)
        self.assertAlmostEqual(sum(p["weight"] / total for p in prizes), 1.0)

    # DS-TS-VIEW-OWN-WINNINGS
    def test_view_own_winnings(self):
        mine = self.new_client()
        other = self.new_client()
        _spin_until(mine, want_recorded=True)
        _spin_until(mine, want_recorded=True)
        _, body = _get(mine, "/api/winnings")
        records = json.loads(body)
        self.assertEqual(len(records), 2)
        self.assertTrue(records[0]["won_at"] >= records[1]["won_at"])
        _, other_body = _get(other, "/api/winnings")
        self.assertEqual(json.loads(other_body), [])

    # DS-TS-NAVIGATE-MENU
    def test_navigate_menu(self):
        client = self.new_client()
        _, html = _get(client, "/")
        self.assertIn('href="#/spin"', html)
        self.assertIn('href="#/prizes"', html)
        self.assertIn('href="#/my-winnings"', html)
        self.assertIn(">Spin<", html)
        self.assertIn(">Prizes<", html)
        self.assertIn(">My Winnings<", html)
        _, script = _get(client, "/static/app.js")
        self.assertIn("renderNavigation", script)

    # DS-TS-PLAYER-NAME-RULE
    def test_player_name_rule(self):
        client = self.new_client()
        status, payload = _post_json(client, "/api/spin", {"display_name": "   "})
        self.assertEqual(status, 200)
        status, payload = _post_json(client, "/api/spin", {"display_name": "x" * 31})
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "Name must be 30 characters or less.")
        status, payload = _post_json(client, "/api/spin", {"display_name": "x" * 30})
        self.assertEqual(status, 200)
        # A blank name is stored as Guest when it wins.
        blank = self.new_client()
        for _ in range(300):
            _, payload = _post_json(blank, "/api/spin", {"display_name": "   "})
            if payload["recorded"]:
                break
        records = json.loads(_get(blank, "/api/winnings")[1])
        self.assertTrue(records, "expected a recorded win with a blank name")
        self.assertTrue(all(r["display_name"] == "Guest" for r in records))

    # DS-TS-NO-PRIZE-NOT-RECORDED
    def test_no_prize_not_recorded(self):
        client = self.new_client()
        for _ in range(300):
            before = len(json.loads(_get(client, "/api/winnings")[1]))
            status, payload = _post_json(client, "/api/spin", {"display_name": "Tester"})
            self.assertEqual(status, 200)
            after = len(json.loads(_get(client, "/api/winnings")[1]))
            if not payload["recorded"]:
                self.assertEqual(payload["prize"]["name"], "Better Luck Next Time")
                self.assertEqual(after, before)
                return
        self.fail("no 'Better Luck Next Time' result in 300 spins")

    # DS-TS-WEIGHTED-DRAW
    def test_weighted_draw(self):
        client = self.new_client()
        prizes = json.loads(_get(client, "/api/prizes")[1])
        total = sum(p["weight"] for p in prizes)
        counts = {p["name"]: 0 for p in prizes}
        runs = 300
        for _ in range(runs):
            status, payload = _post_json(client, "/api/spin", {"display_name": "Tester"})
            self.assertEqual(status, 200)
            counts[payload["prize"]["name"]] += 1
        for p in prizes:
            expected = p["weight"] / total
            observed = counts[p["name"]] / runs
            self.assertLessEqual(abs(observed - expected), 0.08, "%s: %.3f vs %.3f" % (p["name"], observed, expected))

    # DS-TS-RESPONSE-TIME
    def test_response_time(self):
        client = self.new_client()
        slowest = 0.0
        for _ in range(20):
            started = time.perf_counter()
            status, _ = _post_json(client, "/api/spin", {"display_name": "Tester"})
            elapsed = time.perf_counter() - started
            self.assertEqual(status, 200)
            slowest = max(slowest, elapsed)
        self.assertLess(slowest, 1.0)

    # DS-TS-CONCURRENT-SPINS
    def test_concurrent_spins(self):
        clients = [self.new_client() for _ in range(10)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(
                lambda c: _post_json(c, "/api/spin", {"display_name": "Tester"}), clients))
        self.assertTrue(all(status == 200 for status, _ in results))
        recorded_in_responses = sum(1 for _, payload in results if payload["recorded"])
        stored = 0
        for client in clients:
            stored += len(json.loads(_get(client, "/api/winnings")[1]))
        self.assertEqual(stored, recorded_in_responses)


if __name__ == "__main__":
    unittest.main()
