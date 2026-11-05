"""HTTP 層: 画面（HTML）、静的ファイル、JSON の API を返す。"""

import json
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import parse_qs, unquote, urlparse

from app.service import RequestError, SpinService

WEB_ROOT = Path(__file__).resolve().parent.parent / "web"
STATIC_ROOT = WEB_ROOT / "static"

PAGES = {
    "/": "index.html",
    "/rewards": "rewards.html",
    "/my-winnings": "my-winnings.html",
}

# 旧い画面の URL。ブックマークを壊さないように、新しい URL へ転送する。
REDIRECTS = {
    "/prizes": "/rewards",
}

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
}

NOT_FOUND_TEXT = "Page not found"


class WheelRequestHandler(BaseHTTPRequestHandler):
    """1 件の HTTP 要求を受け、画面・静的ファイル・API に振り分けて応答する。"""

    server_version = "WheelOfFortune/1.0"

    def do_GET(self) -> None:
        """GET の要求を画面、静的ファイル、API に振り分ける。"""
        self._route("GET")

    def do_POST(self) -> None:
        """POST の要求を API に振り分ける。"""
        self._route("POST")

    def _route(self, method: str) -> None:
        """振り分けと、例外の利用者向け応答を行う。"""
        try:
            path = urlparse(self.path).path
            if method == "GET" and path in PAGES:
                self.serve_page(PAGES[path])
            elif method == "GET" and path in REDIRECTS:
                self._send_redirect(REDIRECTS[path])
            elif method == "GET" and path.startswith("/static/"):
                self.serve_static(path[len("/static/"):])
            elif method == "GET" and path == "/api/prizes":
                self.handle_prizes()
            elif method == "GET" and path == "/api/winnings":
                self.handle_winnings()
            elif method == "POST" and path == "/api/spins":
                self.handle_spin()
            else:
                self._send_not_found(path.startswith("/api/"))
        except RequestError as error:
            self._send_json(error.status, {"error": error.message})
        except Exception:  # 想定外の例外でもサーバーは止めない
            traceback.print_exc(file=sys.stderr)
            self._send_json(500, {"error": "Something went wrong. Please try again."})

    def serve_page(self, filename: str) -> None:
        """画面の HTML を返す（ナビゲーションは各 HTML に含む）。"""
        self._send_file(WEB_ROOT / filename)

    def _send_redirect(self, location: str) -> None:
        """旧い URL を新しい URL へ 301 で転送する（本文は無し）。"""
        self.send_response(301)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def serve_static(self, relative: str) -> None:
        """static 配下の CSS と JavaScript を返す。範囲外のパスは 404 にする。"""
        requested = (STATIC_ROOT / unquote(relative)).resolve()
        if not _is_inside(requested, STATIC_ROOT) or not requested.is_file():
            self._send_not_found(False)
            return
        self._send_file(requested)

    def handle_prizes(self) -> None:
        """景品一覧を JSON で返す。"""
        prizes = self.server.service.get_prizes()  # type: ignore[attr-defined]
        self._send_json(200, {"prizes": prizes})

    def handle_spin(self) -> None:
        """抽選を行い、結果と当選記録を JSON で返す。"""
        body = self._read_json_body()
        result = self.server.service.spin(body.get("player_name"))  # type: ignore[attr-defined]
        self._send_json(200, result)

    def handle_winnings(self) -> None:
        """名前で絞り込んだ当選記録を JSON で返す。"""
        query = parse_qs(urlparse(self.path).query)
        raw_name = query.get("name", [None])[0]
        result = self.server.service.get_winnings(raw_name)  # type: ignore[attr-defined]
        self._send_json(200, result)

    def _read_json_body(self) -> Dict[str, Any]:
        """要求本文を JSON のオブジェクトとして読む。読めなければ 400 にする。"""
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length > 0 else b""
            body = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise RequestError(400, "Request body must be JSON.")
        if not isinstance(body, dict):
            raise RequestError(400, "Request body must be JSON.")
        return body

    def _send_file(self, path: Path) -> None:
        """ファイルの中身を、拡張子に合った Content-Type で返す。"""
        data = path.read_bytes()
        content_type = CONTENT_TYPES.get(path.suffix, "application/octet-stream")
        self._send_bytes(200, content_type, data)

    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        """JSON の応答を返す。"""
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(status, "application/json; charset=utf-8", data)

    def _send_not_found(self, as_json: bool) -> None:
        """404 を返す。API の要求は JSON、それ以外は文字で返す。"""
        if as_json:
            self._send_json(404, {"error": "Not found"})
        else:
            self._send_bytes(404, "text/plain; charset=utf-8", NOT_FOUND_TEXT.encode("utf-8"))

    def _send_bytes(self, status: int, content_type: str, data: bytes) -> None:
        """ヘッダーと本文を書く。"""
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)


def _is_inside(path: Path, root: Path) -> bool:
    """path が root の内側（root 自身を含む）にあるかを返す。path は解決済みであること。"""
    try:
        path.relative_to(root.resolve())
        return True
    except ValueError:
        return False


def create_server(host: str, port: int, service: SpinService) -> ThreadingHTTPServer:
    """指定の番号で待ち受ける HTTP サーバーを作る。部品（service）は呼び出し側が組み立てる。"""
    server = ThreadingHTTPServer((host, port), WheelRequestHandler)
    server.daemon_threads = True
    server.service = service  # type: ignore[attr-defined]
    return server
