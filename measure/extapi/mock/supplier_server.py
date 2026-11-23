#!/usr/bin/env python3
"""題材 extapi の模擬の外部システム（仕入先「まるいち物産」の在庫照会 API）。標準ライブラリだけで動く。

使い方:
  共用（作業中のエージェントが接続して調べる。v1 と v2 の両方を出す）:
    python3 measure/extapi/mock/supplier_server.py --port 18080 --versions 1,2 --items 180
  採点（hidden/conftest.py が別のポートで起こし、--admin-key で中身を入れ替える）:
    python3 supplier_server.py --port <空きポート> --versions 1 --items 0 --admin-key <鍵>

仕込んである癖（説明書 workdir-files/supplier-api/API仕様書.md と比べたもの）:
  1. ページ分割: v1 は page / per_page。説明書は per_page の上限を 100 と書くが、実物は 50 で黙って切る（食い違い）
  2. 廃番: 説明書は「廃番の商品は返さない」と書くが、実物は discontinued: true を付けて返す（食い違い）
  3. 回数制限: トークンごとに window 秒あたり rate 回まで。超えると 429 と Retry-After（秒）。待たずに来た要求は early_retry に数える
  4. 認証の失効: トークンは token_uses 回の成功、または token_ttl 秒で失効し、401 token_expired を返す（取り直しが要る）
  v2（段 2）: カーソル方式（最後のページは next_cursor のキーが無い。通知は null と書く＝食い違い）、
              在庫が {available, reserved}、廃番が status、回数制限が rate_v2
回数制限と失効は、発行したトークンごとに持つ（複数の実行が同時に使っても混ざらない）。
"""

import argparse
import json
import random
import secrets
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

CLIENT_ID = "maruichi-dev-client"
CLIENT_SECRET = "s3cret-dev-7f2a"
PAGE_CAP = 50
NAMES = ["六角ボルト", "平ワッシャー", "ばね座金", "六角ナット", "皿ねじ", "なべ小ねじ", "アンカーボルト", "Uボルト", "蝶ナット", "寸切りボルト",
         "ステンレス釘", "コーススレッド", "ドリルねじ", "リベット", "割りピン", "止め輪", "平行ピン", "スプリングピン", "アイボルト", "ターンバックル"]


def make_items(count: int, seed: int) -> list:
    rnd = random.Random(seed)
    items = []
    for i in range(1, count + 1):
        items.append({"code": f"MB-{i:05d}", "name": f"{rnd.choice(NAMES)} M{rnd.choice([3, 4, 5, 6, 8, 10, 12])}×{rnd.choice([10, 15, 20, 25, 30, 40, 50])}",
                      "stock": rnd.randint(0, 900), "reserved": rnd.randint(0, 60), "discontinued": rnd.random() < 0.08})
    return items


class State:
    def __init__(self, args) -> None:
        self.lock = threading.Lock()
        self.versions = set(args.versions.split(","))
        self.rate = {"1": args.rate, "2": args.rate_v2}
        self.window = args.window
        self.retry_after = args.retry_after
        self.token_uses = args.token_uses
        self.token_ttl = args.token_ttl
        self.items = make_items(args.items, args.seed)
        self.tokens = {}
        self.fail = {"mode": "none", "after": 0}
        self.reset_stats()

    def reset_stats(self) -> None:
        self.stats = {"data_requests": 0, "data_ok": 0, "token_issued": 0, "r429": 0, "early_retry": 0, "expired_401": 0, "invalid_401": 0, "r503": 0, "max_per_page_seen": 0}
        self.ok_since_fail = 0


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    state = None
    admin_key = None

    def log_message(self, fmt, *a):  # 静かにする
        return

    def send_json(self, status: int, body, headers=None) -> None:
        raw = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(raw)

    def read_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except ValueError:
            return {k: v[0] for k, v in parse_qs(raw.decode(errors="replace")).items()}

    # ---- 管理（採点器だけが使う） ----
    def admin(self, path: str, body: dict) -> None:
        st = self.state
        if not self.admin_key or self.headers.get("X-Admin-Key") != self.admin_key:
            return self.send_json(404, {"error": "not_found"})
        with st.lock:
            if path == "/__admin/set":
                if "items" in body:
                    st.items = body["items"]
                if "fail" in body:
                    st.fail = body["fail"]
                    st.ok_since_fail = 0
                if body.get("reset_stats"):
                    st.reset_stats()
                if body.get("drop_tokens"):
                    st.tokens = {}
                return self.send_json(200, {"ok": True})
            if path == "/__admin/stats":
                return self.send_json(200, dict(st.stats, items=len(st.items)))
        self.send_json(404, {"error": "not_found"})

    # ---- 認証 ----
    def issue_token(self, body: dict) -> None:
        st = self.state
        if body.get("client_id") != CLIENT_ID or body.get("client_secret") != CLIENT_SECRET:
            return self.send_json(401, {"error": "invalid_client"})
        token = secrets.token_hex(16)
        with st.lock:
            st.tokens[token] = {"issued": time.monotonic(), "uses": 0, "hits": deque(), "blocked_until": 0.0}
            st.stats["token_issued"] += 1
        self.send_json(200, {"access_token": token, "token_type": "Bearer", "expires_in": st.token_ttl})

    def check(self, version: str):
        """認証・失効・回数制限・障害を順に見る。通れば None、止めるなら (status, body, headers)。"""
        st = self.state
        auth = self.headers.get("Authorization") or ""
        token = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
        now = time.monotonic()
        with st.lock:
            st.stats["data_requests"] += 1
            if st.fail["mode"] == "down" or (st.fail["mode"] == "after" and st.ok_since_fail >= int(st.fail.get("after", 0))):
                st.stats["r503"] += 1
                return 503, {"error": "service_unavailable"}, {}
            info = st.tokens.get(token)
            if info is None:
                st.stats["invalid_401"] += 1
                return 401, {"error": "invalid_token"}, {}
            if info["uses"] >= st.token_uses or now - info["issued"] > st.token_ttl:
                st.stats["expired_401"] += 1
                return 401, {"error": "token_expired"}, {}
            if now < info["blocked_until"]:
                st.stats["early_retry"] += 1
                st.stats["r429"] += 1
                return 429, {"error": "rate_limited"}, {"Retry-After": str(st.retry_after)}
            hits = info["hits"]
            while hits and now - hits[0] > st.window:
                hits.popleft()
            if len(hits) >= st.rate[version]:
                st.stats["r429"] += 1
                info["blocked_until"] = now + st.retry_after - 0.1  # 告げた秒数を待って来た要求は、少し早く届いても通す
                return 429, {"error": "rate_limited"}, {"Retry-After": str(st.retry_after)}
            hits.append(now)
            info["uses"] += 1
            st.stats["data_ok"] += 1
            st.ok_since_fail += 1
        return None

    def items_v1(self, query: dict) -> None:
        st = self.state
        try:
            page = max(1, int(query.get("page", ["1"])[0]))
            asked = max(1, int(query.get("per_page", ["20"])[0]))
        except ValueError:
            return self.send_json(400, {"error": "bad_request"})
        per_page = min(asked, PAGE_CAP)  # 説明書は上限 100 と書くが、実物は 50 で黙って切る
        with st.lock:
            st.stats["max_per_page_seen"] = max(st.stats["max_per_page_seen"], asked)
            rows = sorted(st.items, key=lambda x: x["code"])
        part = rows[(page - 1) * per_page: page * per_page]
        out = [{"code": r["code"], "name": r["name"], "stock": r["stock"], "discontinued": bool(r.get("discontinued"))} for r in part]
        self.send_json(200, {"items": out, "page": page, "per_page": per_page, "total": len(rows)})

    def items_v2(self, query: dict) -> None:
        st = self.state
        try:
            limit = min(max(1, int(query.get("limit", ["20"])[0])), PAGE_CAP)
        except ValueError:
            return self.send_json(400, {"error": "bad_request"})
        cursor = query.get("cursor", [""])[0]
        with st.lock:
            rows = sorted(st.items, key=lambda x: x["code"])
        if cursor:
            rows = [r for r in rows if r["code"] > cursor]
        part = rows[:limit]
        out = [{"code": r["code"], "name": r["name"], "stock": {"available": r["stock"], "reserved": int(r.get("reserved", 0))},
                "status": "discontinued" if r.get("discontinued") else "active"} for r in part]
        body = {"items": out}
        if len(rows) > limit:
            body["next_cursor"] = part[-1]["code"]  # 最後のページではキーごと無い（通知は null と書く）
        self.send_json(200, body)

    def route(self, method: str) -> None:
        url = urlparse(self.path)
        path = url.path.rstrip("/") or "/"
        body = self.read_body() if method == "POST" else {}
        if path.startswith("/__admin/"):
            return self.admin(path, body)
        parts = path.split("/")
        version = parts[1][1:] if len(parts) > 1 and parts[1] in ("v1", "v2") else None
        if version is None:
            return self.send_json(404, {"error": "not_found"})
        if version not in self.state.versions:
            if version == "1":
                return self.send_json(410, {"error": "gone", "message": "v1 は終了しました。v2 を使ってください"})
            return self.send_json(404, {"error": "not_found"})
        rest = "/" + "/".join(parts[2:])
        if rest == "/auth/token" and method == "POST":
            return self.issue_token(body)
        if rest == "/items" and method == "GET":
            stop = self.check(version)
            if stop:
                return self.send_json(stop[0], stop[1], stop[2])
            query = parse_qs(url.query)
            return self.items_v1(query) if version == "1" else self.items_v2(query)
        self.send_json(404, {"error": "not_found"})

    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=18080)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--versions", default="1,2")
    parser.add_argument("--items", type=int, default=180)
    parser.add_argument("--seed", type=int, default=20261123)
    parser.add_argument("--rate", type=int, default=3, help="v1: window 秒あたりの回数")
    parser.add_argument("--rate-v2", type=int, default=2, help="v2: window 秒あたりの回数")
    parser.add_argument("--window", type=float, default=1.0)
    parser.add_argument("--retry-after", type=int, default=1)
    parser.add_argument("--token-uses", type=int, default=6, help="トークン 1 つで成功できる照会の回数")
    parser.add_argument("--token-ttl", type=int, default=30, help="トークンの有効秒数")
    parser.add_argument("--admin-key", default=None)
    args = parser.parse_args()
    Handler.state = State(args)
    Handler.admin_key = args.admin_key
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.daemon_threads = True
    print(f"supplier mock: http://{args.host}:{args.port} versions={args.versions} items={args.items}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
