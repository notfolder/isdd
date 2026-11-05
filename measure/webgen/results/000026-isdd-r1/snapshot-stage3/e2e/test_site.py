"""E2E テスト: 実サーバー（src/main.py を子プロセスで起動）に HTTP で問い合わせ、要件 7 章のシナリオを確かめる。

標準ライブラリだけ（unittest と urllib）。ブラウザは使わない。
"""

import os
import re
import socket
import subprocess
import sys
import tempfile
import http.cookiejar
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request

PROJECT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAIN = os.path.join(PROJECT, "src", "main.py")
VOTE_ERROR = "Please select one option before you vote."


def free_port():
    """空いている 127.0.0.1 のポート番号を返す。"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def browser():
    """Cookie を保持する HTTP クライアント（同じ opener を使えば同じブラウザとして振る舞う）。"""
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def fetch(url, data=None, opener=None):
    """GET（data が None のとき）または POST を行い、(状態コード, 最終 URL, 本文) を返す。リダイレクトは追う。"""
    body = urllib.parse.urlencode(data).encode("utf-8") if data is not None else None
    request = urllib.request.Request(url, data=body)
    open_url = opener.open if opener is not None else urllib.request.urlopen
    try:
        with open_url(request, timeout=10) as response:
            return response.status, response.geturl(), response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        return error.code, error.geturl(), error.read().decode("utf-8")


class Site:
    """src/main.py を子プロセスとして起動する。終了は stop() で行う。"""

    def __init__(self, data_dir):
        self.port = free_port()
        self.base = "http://127.0.0.1:%d" % self.port
        env = dict(os.environ, PORT=str(self.port), DATA_DIR=data_dir)
        self.proc = subprocess.Popen(
            [sys.executable, MAIN],
            cwd=PROJECT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        self._wait_until_ready()

    def _wait_until_ready(self):
        deadline = time.time() + 30
        while time.time() < deadline:
            if self.proc.poll() is not None:
                output = self.proc.stdout.read().decode("utf-8", "replace")
                raise RuntimeError("server exited early:\n" + output)
            try:
                fetch(self.base + "/")
                return
            except OSError:
                time.sleep(0.2)
        raise RuntimeError("server did not start in time")

    def stop(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
        if self.proc.stdout:
            self.proc.stdout.close()


def option_id(page, text):
    """詳細画面の HTML から、選択肢の名前に対応する option_id を取り出す。"""
    match = re.search(r'value="(\d+)">\s*%s\s*<' % re.escape(text), page)
    if match is None:
        raise AssertionError("option not found on page: " + text)
    return match.group(1)


def votes_for(page, text):
    """結果画面の HTML から、選択肢の票数を取り出す。"""
    match = re.search(r"<td>%s</td>\s*<td>(\d+)</td>" % re.escape(text), page)
    if match is None:
        raise AssertionError("option row not found on page: " + text)
    return int(match.group(1))


class PollsSiteTest(unittest.TestCase):
    """サンプルデータ入りの実サーバーに対するシナリオ（要件定義書 7 章）。"""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.site = Site(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.site.stop()
        cls.tmp.cleanup()

    def test_browse_poll_list(self):
        status, _, page = fetch(self.site.base + "/")
        self.assertEqual(status, 200)
        self.assertEqual(page.count('<li class="card">'), 3)
        self.assertIn("Which programming language do you like most?", page)
        self.assertIn("<h1>Surveys</h1>", page)
        match = re.search(r'href="(/surveys/\d+)">Vote<', page)
        self.assertIsNotNone(match, "no Vote link on the list")
        status, final_url, detail = fetch(self.site.base + match.group(1))
        self.assertEqual(status, 200)
        self.assertIn('name="option_id"', detail)

    def test_view_poll_options(self):
        status, _, page = fetch(self.site.base + "/surveys/1")
        self.assertEqual(status, 200)
        self.assertIn("Which programming language do you like most?", page)
        for text in ("Python", "JavaScript", "Go", "Rust"):
            self.assertIn(text, page)
        self.assertEqual(page.count('type="radio"'), 4)
        self.assertIn(">Vote</button>", page)

    def test_cast_vote_once_per_poll(self):
        voter = browser()
        stranger = browser()
        base = self.site.base
        before = votes_for(fetch(base + "/surveys/3/results")[2], "Dark mode")

        dark_mode = option_id(fetch(base + "/surveys/3", opener=voter)[2], "Dark mode")
        status, final_url, page = fetch(base + "/surveys/3/vote", {"option_id": dark_mode}, opener=voter)
        self.assertEqual(status, 200)
        self.assertIn("voted=1", final_url)
        self.assertIn("Thank you for voting.", page)
        self.assertEqual(votes_for(page, "Dark mode"), before + 1)

        status, _, detail = fetch(base + "/surveys/3", opener=voter)
        self.assertEqual(status, 200)
        self.assertIn("You have already voted", detail)
        self.assertEqual(len(re.findall(r'<input type="radio"[^>]*\sdisabled', detail)), 3)
        self.assertIn('class="button" disabled>Vote</button>', detail)

        status, _, page = fetch(base + "/surveys/3/vote", {"option_id": dark_mode}, opener=voter)
        self.assertEqual(status, 409)
        self.assertIn("You have already voted", page)
        _, _, results = fetch(base + "/surveys/3/results")
        self.assertEqual(votes_for(results, "Dark mode"), before + 1)

        status, _, _ = fetch(base + "/surveys/3/vote", {"option_id": dark_mode}, opener=stranger)
        self.assertEqual(status, 200)
        _, _, results = fetch(base + "/surveys/3/results")
        self.assertEqual(votes_for(results, "Dark mode"), before + 2)

    def test_color_theme(self):
        base = self.site.base
        stylesheet = None
        for path in ("/", "/surveys/1", "/surveys/1/results", "/results"):
            status, _, page = fetch(base + path)
            self.assertEqual(status, 200, path)
            match = re.search(r'href="(/static/style\.css)"', page)
            self.assertIsNotNone(match, path)
            stylesheet = match.group(1)
        status, _, css = fetch(base + stylesheet)
        self.assertEqual(status, 200)
        upper = css.upper()
        self.assertIn("#FFFFE0", upper)
        self.assertIn("#2F4F4F", upper)
        self.assertIsNone(re.search(r"#FFFFFF\b|#FFF\b|#000080\b", upper))
        self.assertNotIn("NAVY", upper)
        self.assertNotIn("WHITE", upper)

    def test_no_poll_word_in_ui(self):
        base = self.site.base
        voter = browser()
        winter = option_id(fetch(base + "/surveys/2", opener=voter)[2], "Winter")
        status, _, voted_page = fetch(base + "/surveys/2/vote", {"option_id": winter}, opener=voter)
        self.assertEqual(status, 200)
        status, _, already_page = fetch(base + "/surveys/2", opener=voter)
        self.assertEqual(status, 200)
        pages = [
            fetch(base + "/")[2],
            fetch(base + "/surveys/1")[2],
            fetch(base + "/surveys/1/results")[2],
            fetch(base + "/results")[2],
            fetch(base + "/surveys/9999")[2],
            voted_page,
            already_page,
        ]
        for page in pages:
            self.assertIsNone(re.search(r"poll", page, re.IGNORECASE), page[:200])
        self.assertIn("Surveys", pages[0])
        self.assertIn("Surveys", pages[4])

    def test_reject_invalid_vote(self):
        _, _, before_page = fetch(self.site.base + "/surveys/1/results")
        before = votes_for(before_page, "Python")

        status, _, page = fetch(self.site.base + "/surveys/1/vote", {})
        self.assertEqual(status, 400)
        self.assertIn(VOTE_ERROR, page)

        other_poll_option = option_id(fetch(self.site.base + "/surveys/2")[2], "Winter")
        status, _, page = fetch(
            self.site.base + "/surveys/1/vote", {"option_id": other_poll_option}
        )
        self.assertEqual(status, 400)
        self.assertIn(VOTE_ERROR, page)

        status, _, page = fetch(self.site.base + "/surveys/1/vote", {"option_id": "999999"})
        self.assertEqual(status, 400)
        self.assertIn(VOTE_ERROR, page)

        _, _, after_page = fetch(self.site.base + "/surveys/1/results")
        self.assertEqual(votes_for(after_page, "Python"), before)

        status, _, page = fetch(self.site.base + "/surveys/9999")
        self.assertEqual(status, 404)
        self.assertIn("Not found", page)
        self.assertIn('href="/"', page)

    def test_view_all_results(self):
        status, _, page = fetch(self.site.base + "/results")
        self.assertEqual(status, 200)
        for question in (
            "Which programming language do you like most?",
            "What is your favorite season?",
            "Which feature would you like to see next?",
        ):
            self.assertIn(question, page)
        self.assertIn("Dark mode", page)
        match = re.search(r'href="(/surveys/\d+/results)">Details<', page)
        self.assertIsNotNone(match, "no Details link on the overview")
        status, _, detail = fetch(self.site.base + match.group(1))
        self.assertEqual(status, 200)
        self.assertIn("Total votes", detail)

    def test_navigate_menu(self):
        pages = {
            "/": "Surveys",
            "/surveys/1": "Surveys",
            "/surveys/1/results": "Results",
            "/results": "Results",
        }
        for path, active_label in pages.items():
            status, _, page = fetch(self.site.base + path)
            self.assertEqual(status, 200, path)
            self.assertIn('href="/results"', page, path)
            self.assertIn('href="/"', page, path)
            self.assertRegex(
                page,
                r'class="active" aria-current="page"[^>]*>%s<' % active_label,
                path,
            )
        status, final_url, _ = fetch(self.site.base + "/results")
        self.assertEqual(status, 200)
        self.assertEqual(final_url, self.site.base + "/results")

    def test_sample_data_on_empty_start(self):
        with tempfile.TemporaryDirectory() as data_dir:
            first = Site(data_dir)
            try:
                _, _, page = fetch(first.base + "/")
                self.assertEqual(page.count('<li class="card">'), 3)
            finally:
                first.stop()
            second = Site(data_dir)
            try:
                _, _, page = fetch(second.base + "/")
                self.assertEqual(page.count('<li class="card">'), 3)
            finally:
                second.stop()


if __name__ == "__main__":
    unittest.main()
