"""E2E テスト用の実サーバー起動の補助。

テストごとに一時フォルダを作り、run.sh を子プロセスとして起動する。
停止は自分が起動したプロセスの PID に対してだけ行う。
"""

import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """リダイレクトを追わず、303 の応答をそのまま返す。"""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


class Response:
    """HTTP の応答（ステータス、ヘッダー、本文の文字列）。"""

    def __init__(self, status, headers, body):
        self.status = status
        self.headers = headers
        self.body = body


def _free_port():
    """空いている port を 1 つ選ぶ。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class SiteServer:
    """run.sh で起動したサイト。stop で自分のプロセスだけを止める。"""

    def __init__(self, data_dir=None):
        """data_dir を省略すると一時フォルダに空の DATA_DIR を作る。"""
        self.workdir = tempfile.mkdtemp(prefix="species-e2e-")
        self.data_dir = data_dir or os.path.join(self.workdir, "data")
        self.port = _free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        self._log_path = os.path.join(self.workdir, "server.log")
        env = dict(os.environ, PORT=str(self.port), DATA_DIR=self.data_dir)
        with open(self._log_path, "w") as log:
            self.process = subprocess.Popen(
                ["bash", "run.sh"], cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT
            )
        self._wait_until_ready()

    def _wait_until_ready(self):
        """応答できるまで待つ。起動できなければ例外にする。"""
        deadline = time.time() + 15
        while time.time() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError("run.sh exited early:\n" + self.log())
            try:
                self.request("GET", "/")
                return
            except (urllib.error.URLError, ConnectionError, OSError):
                time.sleep(0.1)
        raise RuntimeError("server did not start:\n" + self.log())

    def request(self, method, path, form=None):
        """リダイレクトを追わずに要求する。404 や 500 も Response として返す。"""
        data = None
        if form is not None:
            data = urllib.parse.urlencode(form).encode("utf-8")
        req = urllib.request.Request(self.base + path, data=data, method=method)
        try:
            with _OPENER.open(req, timeout=10) as resp:
                return Response(resp.status, resp.headers, resp.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            return Response(error.code, error.headers, error.read().decode("utf-8"))

    def log(self):
        """サーバーの標準出力・標準エラーの内容。"""
        try:
            with open(self._log_path, encoding="utf-8", errors="replace") as handle:
                return handle.read()
        except OSError:
            return ""

    def stop(self):
        """自分が起動したプロセスだけを止める。"""
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        shutil.rmtree(self.workdir, ignore_errors=True)


def result_count(body):
    """一覧画面の件数（結果が無いときは None）。"""
    marker = '<p class="result-count">'
    if marker not in body:
        return None
    start = body.index(marker) + len(marker)
    return int(body[start:].split(" ", 1)[0])
