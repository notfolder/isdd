"""HTTP server for the wheel of fortune website (standard library only)."""

import json
import os
import re
import secrets
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple

from draw import pick_prize
from store import Store

HERE = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(HERE, "web")
COOKIE_NAME = "wof_player"
COOKIE_MAX_AGE = 365 * 24 * 60 * 60
MAX_NAME_LENGTH = 30
PLAYER_KEY_PATTERN = re.compile(r"^[0-9a-f]{32}$")
STATIC_TYPES = {
    "index.html": "text/html; charset=utf-8",
    "style.css": "text/css; charset=utf-8",
    "app.js": "application/javascript; charset=utf-8",
}
MSG_INVALID = "Invalid request."
MSG_NAME_TOO_LONG = "Name must be 30 characters or less."
MSG_NO_PRIZES = "No prizes are available yet."
MSG_UNEXPECTED = "Something went wrong. Please try again."


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class WheelRequestHandler(BaseHTTPRequestHandler):
    """Serves the web pages and the JSON endpoints used by the pages."""

    server_version = "WheelOfFortune/1.0"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - base signature
        """Suppress per-request access logs; errors are still reported."""
        return

    @property
    def store(self) -> Store:
        return self.server.store  # type: ignore[attr-defined]

    def do_GET(self) -> None:  # noqa: N802 - required by http.server
        try:
            path = self.path.split("?", 1)[0]
            if path == "/api/prizes":
                self.handle_prizes()
            elif path == "/api/winnings":
                self.handle_winnings()
            elif path == "/":
                self._send_static("index.html")
            elif path.startswith("/static/"):
                self._send_static(path[len("/static/"):])
            else:
                self._send_json(404, {"error": "Not found."})
        except Exception:  # pragma: no cover - reported to the client
            self._report_unexpected()

    def do_POST(self) -> None:  # noqa: N802 - required by http.server
        try:
            path = self.path.split("?", 1)[0]
            if path == "/api/spin":
                self.handle_spin()
            else:
                self._send_json(404, {"error": "Not found."})
        except Exception:  # pragma: no cover - reported to the client
            self._report_unexpected()

    # --- endpoints -------------------------------------------------------

    def handle_spin(self) -> None:
        """POST /api/spin: draw one prize, record it when it is a win."""
        player_key, new_cookie = self._player_key()
        body = self._read_json_body()
        if body is None:
            self._send_json(400, {"error": MSG_INVALID}, new_cookie)
            return
        raw_name = body.get("display_name", "")
        if not isinstance(raw_name, str):
            self._send_json(400, {"error": MSG_INVALID}, new_cookie)
            return
        name = raw_name.strip() or "Guest"
        if len(name) > MAX_NAME_LENGTH:
            self._send_json(400, {"error": MSG_NAME_TOO_LONG}, new_cookie)
            return
        prizes = self.store.list_prizes()
        if not prizes:
            self._send_json(503, {"error": MSG_NO_PRIZES}, new_cookie)
            return
        prize = pick_prize(prizes, secrets.SystemRandom().random())
        recorded = False
        if prize["is_win"]:
            self.store.add_winning(player_key, name, prize["name"], _now_utc_iso())
            recorded = True
        payload = {
            "prize": {
                "id": prize["id"],
                "name": prize["name"],
                "is_win": prize["is_win"],
                "position": prize["position"],
            },
            "recorded": recorded,
        }
        self._send_json(200, payload, new_cookie)

    def handle_prizes(self) -> None:
        """GET /api/prizes: the prize list in display order."""
        self._send_json(200, self.store.list_prizes())

    def handle_winnings(self) -> None:
        """GET /api/winnings: the current browser's winning records, newest first."""
        player_key, new_cookie = self._player_key()
        self._send_json(200, self.store.list_winnings(player_key), new_cookie)

    # --- helpers ---------------------------------------------------------

    def _player_key(self) -> Tuple[str, Optional[str]]:
        """Return (player key, new cookie value or None).

        A new random key is issued when the browser has no valid cookie.
        """
        raw_cookie = self.headers.get("Cookie", "")
        for part in raw_cookie.split(";"):
            name, _, value = part.strip().partition("=")
            if name == COOKIE_NAME and PLAYER_KEY_PATTERN.match(value):
                return value, None
        key = secrets.token_hex(16)
        return key, key

    def _read_json_body(self) -> Optional[Dict[str, Any]]:
        """Parse the JSON body. An empty body counts as an empty object."""
        length = int(self.headers.get("Content-Length") or 0)
        if length == 0:
            return {}
        if length > 4096:
            return None
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None
        return data if isinstance(data, dict) else None

    def _send_json(self, status: int, payload: Any, new_cookie: Optional[str] = None) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self._send_cookie(new_cookie)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_cookie(self, new_cookie: Optional[str]) -> None:
        if new_cookie:
            self.send_header(
                "Set-Cookie",
                f"{COOKIE_NAME}={new_cookie}; Path=/; Max-Age={COOKIE_MAX_AGE}; HttpOnly; SameSite=Lax",
            )

    def _send_static(self, name: str) -> None:
        content_type = STATIC_TYPES.get(name)
        if content_type is None:
            self._send_json(404, {"error": "Not found."})
            return
        with open(os.path.join(WEB_DIR, name), "rb") as handle:
            body = handle.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _report_unexpected(self) -> None:
        import traceback

        traceback.print_exc(file=sys.stderr)
        try:
            self._send_json(500, {"error": MSG_UNEXPECTED})
        except OSError:
            pass


def build_server(port: int, data_dir: str) -> ThreadingHTTPServer:
    """Create the HTTP server on 127.0.0.1 with the sample prizes in place.

    Port 0 asks the system for a free port (used by the tests).
    """
    store = Store(os.path.join(data_dir, "wheel.sqlite3"))
    store.seed_sample_prizes()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), WheelRequestHandler)
    httpd.daemon_threads = True
    httpd.store = store  # type: ignore[attr-defined]
    return httpd


def main() -> None:
    """Start the server using PORT and DATA_DIR from the environment."""
    port = int(os.environ.get("PORT", "8000"))
    data_dir = os.environ.get("DATA_DIR") or os.path.join(os.getcwd(), "data")
    os.makedirs(data_dir, exist_ok=True)
    httpd = build_server(port, data_dir)
    print(f"Wheel of Fortune is running at http://127.0.0.1:{port}  (data: {data_dir})", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
