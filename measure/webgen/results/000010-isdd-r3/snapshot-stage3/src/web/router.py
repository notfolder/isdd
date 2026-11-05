"""HTTP 要求を画面の配信か API の呼び出しに振り分ける。"""

import json
import mimetypes
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from web import api

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
PAGE_FILES = {"/": "index.html", "/rewards": "rewards.html", "/records": "records.html"}


class RequestHandler(BaseHTTPRequestHandler):
    """画面（HTML・CSS・JavaScript）と API の要求を受ける。サービスは server の wheel_service を使う。"""

    server_version = "RewardWheel/1.0"

    def do_GET(self) -> None:
        """GET を振り分ける。想定外の例外は 500 の JSON にする。"""
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/rewards":
                status, payload = api.handle_list_prizes(self.server.wheel_service)
                self.send_json(status, payload)
            elif parsed.path == "/api/records":
                values = parse_qs(parsed.query).get("player_name")
                raw_name = values[0] if values else None
                status, payload = api.handle_list_records(self.server.wheel_service, raw_name)
                self.send_json(status, payload)
            elif parsed.path in PAGE_FILES:
                self.send_static_file(PAGE_FILES[parsed.path])
            elif parsed.path.startswith("/static/"):
                self.send_static_file(parsed.path[len("/static/"):])
            else:
                self.send_text(404, "Not found")
        except Exception:
            self.report_unexpected_error()

    def do_POST(self) -> None:
        """POST を振り分ける。対象は /api/spin だけ。"""
        parsed = urlparse(self.path)
        try:
            if parsed.path != "/api/spin":
                self.send_text(404, "Not found")
                return
            status, payload = api.handle_spin(self.server.wheel_service, self.read_json_body())
            self.send_json(status, payload)
        except Exception:
            self.report_unexpected_error()

    def read_json_body(self) -> Any:
        """本文を JSON として読む。読めなければ None を返す（API 側で 400 になる）。"""
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length > 0 else b""
        try:
            return json.loads(raw.decode("utf-8") or "null")
        except ValueError:
            return None

    def send_static_file(self, relative: str) -> None:
        """static フォルダの中のファイルだけを返す。外へ出るパスや無いファイルは 404。"""
        root = os.path.realpath(STATIC_DIR)
        target = os.path.realpath(os.path.join(root, unquote(relative)))
        if not target.startswith(root + os.sep) or not os.path.isfile(target):
            self.send_text(404, "Not found")
            return
        with open(target, "rb") as handle:
            body = handle.read()
        content_type = mimetypes.guess_type(target)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in ("application/javascript", "text/javascript"):
            content_type += "; charset=utf-8"
        self.send_bytes(200, content_type, body)

    def send_json(self, status: int, payload: Any) -> None:
        """JSON の応答を返す。"""
        body = json.dumps(payload).encode("utf-8")
        self.send_bytes(status, "application/json; charset=utf-8", body)

    def send_text(self, status: int, text: str) -> None:
        """短い文字列の応答を返す。"""
        self.send_bytes(status, "text/plain; charset=utf-8", text.encode("utf-8"))

    def send_bytes(self, status: int, content_type: str, body: bytes) -> None:
        """ヘッダーと本文を返す。キャッシュはさせない（当選結果が古い画面で残らないように）。"""
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def report_unexpected_error(self) -> None:
        """想定外の例外を標準エラーに出し、利用者には 500 の JSON を返す。"""
        traceback.print_exc(file=sys.stderr)
        try:
            self.send_json(500, {"error": api.SERVER_ERROR_MESSAGE})
        except OSError:
            pass
