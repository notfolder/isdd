#!/usr/bin/env python3
"""確かめ用の正しい実装 B（作りを変えたもの。JSON ファイルに保存、ページは空になるまで読む、
要求の間隔を自分で空けて 429 を避ける、トークンは取り込みのたびに取り直し、401 でも取り直す）。REF_API_VERSION=2 で v2。"""
import json
import os
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

V2 = os.environ.get("REF_API_VERSION", "1") == "2"
ROOT = os.environ["SUPPLIER_API_URL"] + ("/v2" if V2 else "/v1")
STORE = Path(os.environ.get("DATA_DIR", "data")) / "store.json"
LOCK = threading.Lock()


def load():
    if STORE.exists():
        return json.loads(STORE.read_text(encoding="utf-8"))
    return {"items": {}, "prices": {}, "last_result": None, "last_success_at": None}


def save(state):
    STORE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STORE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, STORE)


class Client:
    def __init__(self):
        self.token = None
        self.last = 0.0
        self.gap = 0.55 if V2 else 0.37

    def request(self, method, path, payload=None, auth=True):
        headers = {"Content-Type": "application/json"}
        if auth:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(ROOT + path, data=json.dumps(payload).encode() if payload is not None else None, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                return res.status, json.loads(res.read()), dict(res.headers)
        except urllib.error.HTTPError as e:
            return e.code, {}, dict(e.headers)

    def login(self):
        status, body, _ = self.request("POST", "/auth/token", {"client_id": os.environ["SUPPLIER_CLIENT_ID"], "client_secret": os.environ["SUPPLIER_CLIENT_SECRET"]}, auth=False)
        if status != 200:
            raise IOError("login failed")
        self.token = body["access_token"]

    def items(self, query):
        attempts = 0
        while True:
            attempts += 1
            if attempts > 6:
                raise IOError("give up")
            wait = self.gap - (time.monotonic() - self.last)
            if wait > 0:
                time.sleep(wait)
            if self.token is None:
                self.login()
            status, body, headers = self.request("GET", "/items?" + query)
            self.last = time.monotonic()
            if status == 200:
                return body
            if status == 401:
                self.token = None
            elif status == 429:
                time.sleep(int(headers.get("Retry-After", "1")) + 0.1)
            else:
                raise IOError(f"status {status}")


def keep(found, row, stock, discontinued):
    if discontinued and stock < 1:
        return
    found[row["code"]] = {"name": row["name"], "stock": stock if stock >= 6 else 0}


def pull():
    client = Client()
    found = {}
    if V2:
        cursor = None
        while True:
            body = client.items("limit=50" + (f"&cursor={cursor}" if cursor else ""))
            for row in body["items"]:
                keep(found, row, row["stock"]["available"], row["status"] != "active")
            cursor = body.get("next_cursor")
            if not cursor:
                break
    else:
        page = 1
        while True:
            body = client.items(f"page={page}&per_page=50")
            if not body["items"]:
                break
            for row in body["items"]:
                keep(found, row, row["stock"], row.get("discontinued", False))
            page += 1
    return found


def do_sync():
    with LOCK:
        state = load()
        try:
            state["items"] = pull()
            state["last_result"] = "ok"
            state["last_success_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        except Exception:
            state["last_result"] = "failed"
        save(state)
        return state["last_result"]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, code, payload, kind="application/json"):
        data = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def listing(self):
        state = load()
        return [{"code": c, "name": v["name"], "stock": v["stock"], "price": state["prices"].get(c)} for c, v in sorted(state["items"].items())]

    def do_GET(self):
        if self.path == "/api/items":
            self.reply(200, self.listing())
        elif self.path == "/api/status":
            state = load()
            self.reply(200, {"last_result": state["last_result"], "last_success_at": state["last_success_at"]})
        elif self.path == "/":
            self.reply(200, ("<h1>在庫</h1><ul>" + "".join(f"<li>{r['code']} {r['name']} {r['stock']}</li>" for r in self.listing()) + "</ul>").encode(), "text/html; charset=utf-8")
        else:
            self.reply(404, {})

    def do_POST(self):
        if self.path == "/api/sync":
            result = do_sync()
            self.reply(200 if result == "ok" else 502, {"result": result})
        else:
            self.reply(404, {})

    def do_PUT(self):
        seg = self.path.strip("/").split("/")
        if len(seg) == 4 and seg[0] == "api" and seg[1] == "items" and seg[3] == "price":
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            with LOCK:
                state = load()
                if payload["price"] is None:
                    state["prices"].pop(seg[2], None)
                else:
                    state["prices"][seg[2]] = payload["price"]
                save(state)
            self.reply(200, {"code": seg[2], "price": payload["price"]})
        else:
            self.reply(404, {})


HTTPServer(("127.0.0.1", int(os.environ.get("PORT", "8000"))), Handler).serve_forever()
