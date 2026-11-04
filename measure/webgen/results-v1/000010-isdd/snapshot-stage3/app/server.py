"""HTTP の経路、JSON API、静的ファイルの配信。"""

import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from app.draw import draw_prize
from app.repository import (
    delete_all_records,
    delete_prize,
    find_records_by_name,
    insert_prize,
    insert_spin_record,
    list_prizes,
)
from app.validation import validate_player_name, validate_prize_name

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
}


def handle_prizes(db_path):
    """GET /api/prizes。景品の一覧を返す。"""
    return 200, {"prizes": list_prizes(db_path)}


def handle_spin(db_path, raw_body):
    """POST /api/spin。利用者名を検証し、景品を 1 件抽選して記録する。"""
    try:
        data = json.loads(raw_body or b"{}")
        if not isinstance(data, dict):
            raise ValueError("not an object")
    except ValueError:
        return 400, {"error": "Invalid request"}
    try:
        player_name = validate_player_name(data.get("player_name"))
    except ValueError as error:
        return 400, {"error": str(error)}
    prizes = list_prizes(db_path)
    if not prizes:
        return 409, {"error": "No prizes are available"}
    index = draw_prize(prizes)
    prize = prizes[index]
    spun_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        record = insert_spin_record(db_path, player_name, prize["id"], prize["name"], spun_at)
    except sqlite3.Error as error:
        print(f"spin record insert failed: {error}", file=sys.stderr)
        return 500, {"error": "Something went wrong. Please try again."}
    return 200, {"prize": prize, "index": index, "record": record}


def handle_add_prize(db_path, raw_body):
    """POST /api/prizes。景品名を検証し、景品を 1 件追加する。"""
    try:
        data = json.loads(raw_body or b"{}")
        if not isinstance(data, dict):
            raise ValueError("not an object")
    except ValueError:
        return 400, {"error": "Invalid request"}
    try:
        name = validate_prize_name(data.get("name"))
    except ValueError as error:
        return 400, {"error": str(error)}
    try:
        prize = insert_prize(db_path, name)
    except sqlite3.Error as error:
        print(f"prize insert failed: {error}", file=sys.stderr)
        return 500, {"error": "Something went wrong. Please try again."}
    return 201, {"prize": prize}


def handle_delete_prize(db_path, id_text):
    """DELETE /api/prizes/{id}。景品を 1 件削除する。抽選記録は残す。"""
    try:
        prize_id = int(id_text)
    except ValueError:
        return 404, {"error": "Prize not found"}
    try:
        deleted = delete_prize(db_path, prize_id)
    except sqlite3.Error as error:
        print(f"prize delete failed: {error}", file=sys.stderr)
        return 500, {"error": "Something went wrong. Please try again."}
    if deleted == 0:
        return 404, {"error": "Prize not found"}
    return 200, {"deleted_id": prize_id}


def handle_records(db_path, query_string):
    """GET /api/records?player_name=。利用者名の抽選記録を新しい順に返す。"""
    values = parse_qs(query_string).get("player_name", [""])
    try:
        player_name = validate_player_name(values[0])
    except ValueError:
        return 400, {"error": "Please enter your name"}
    return 200, {"records": find_records_by_name(db_path, player_name)}


def handle_clear_records(db_path):
    """DELETE /api/records。すべての抽選記録を削除する。景品は消さない。"""
    try:
        deleted = delete_all_records(db_path)
    except sqlite3.Error as error:
        print(f"records delete failed: {error}", file=sys.stderr)
        return 500, {"error": "Something went wrong. Please try again."}
    return 200, {"deleted": deleted}


def serve_static(path):
    """静的ファイルを返す。戻り値は (状態, 内容の種類, 本文)。"""
    entry = STATIC_FILES.get(path)
    if entry is None:
        return 404, "application/json; charset=utf-8", json.dumps({"error": "Not found"}).encode("utf-8")
    filename, content_type = entry
    with open(os.path.join(STATIC_DIR, filename), "rb") as handle:
        return 200, content_type, handle.read()


class _RequestHandler(BaseHTTPRequestHandler):
    """経路を振り分ける。応答は JSON か静的ファイル。"""

    server_version = "WheelOfFortune"

    def do_GET(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/prizes":
                self._send_json(*handle_prizes(self.server.db_path))
            elif parsed.path == "/api/records":
                self._send_json(*handle_records(self.server.db_path, parsed.query))
            elif parsed.path.startswith("/api/"):
                self._send_json(404, {"error": "Not found"})
            else:
                self._send_bytes(*serve_static(parsed.path))
        except Exception as error:  # 想定外の例外は利用者に内部の詳細を見せない
            print(f"unexpected error: {error!r}", file=sys.stderr)
            self._send_json(500, {"error": "Internal error"})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path not in ("/api/spin", "/api/prizes"):
            self._send_json(404, {"error": "Not found"})
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(length) if length > 0 else b""
        handler = handle_spin if parsed.path == "/api/spin" else handle_add_prize
        try:
            self._send_json(*handler(self.server.db_path, body))
        except Exception as error:
            print(f"unexpected error: {error!r}", file=sys.stderr)
            self._send_json(500, {"error": "Internal error"})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/records":
            try:
                self._send_json(*handle_clear_records(self.server.db_path))
            except Exception as error:
                print(f"unexpected error: {error!r}", file=sys.stderr)
                self._send_json(500, {"error": "Internal error"})
            return
        prefix = "/api/prizes/"
        if not parsed.path.startswith(prefix):
            self._send_json(404, {"error": "Not found"})
            return
        try:
            self._send_json(*handle_delete_prize(self.server.db_path, parsed.path[len(prefix):]))
        except Exception as error:
            print(f"unexpected error: {error!r}", file=sys.stderr)
            self._send_json(500, {"error": "Internal error"})

    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(status, "application/json; charset=utf-8", body)

    def _send_bytes(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """標準エラーへの既定の要求ログは出さない。"""
        return
