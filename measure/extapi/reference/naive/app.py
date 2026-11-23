#!/usr/bin/env python3
"""確かめ用の「説明書どおりに素直に作った」実装。
per_page=100 で total から回数を決める、429 と 401 を考えない、返ってきた商品を全部出す（説明書は廃番を返さないと書く）、
取り込みは全部消してから 1 ページずつ入れる（売価も一緒に消える、途中で失敗すると半端に残る）。
REF_API_VERSION=2 では通知どおり: next_cursor が null になるまで読む、在庫は available と reserved の合計。"""
import json
import math
import os
import sqlite3
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

V2 = os.environ.get("REF_API_VERSION", "1") == "2"
BASE = os.environ.get("SUPPLIER_API_URL", "http://127.0.0.1:18080") + ("/v2" if V2 else "/v1")
DATA = Path(os.environ.get("DATA_DIR", "data"))
DATA.mkdir(parents=True, exist_ok=True)


def db():
    con = sqlite3.connect(DATA / "app.db", isolation_level=None)
    con.execute("create table if not exists items(code text primary key, name text, stock integer, price integer)")
    con.execute("create table if not exists meta(k text primary key, v text)")
    return con


def api(method, path, body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body else None, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as res:
        return json.loads(res.read())


def sync():
    con = db()
    token = api("POST", "/auth/token", {"client_id": os.environ.get("SUPPLIER_CLIENT_ID"), "client_secret": os.environ.get("SUPPLIER_CLIENT_SECRET")})["access_token"]
    con.execute("delete from items")
    if V2:
        cursor = None
        while True:
            body = api("GET", "/items?limit=50" + (f"&cursor={cursor}" if cursor else ""), token=token)
            for r in body["items"]:
                if r["status"] == "active":
                    con.execute("insert into items values(?,?,?,null)", (r["code"], r["name"], r["stock"]["available"] + r["stock"]["reserved"]))
            cursor = body["next_cursor"]
            if cursor is None:
                break
    else:
        first = api("GET", "/items?page=1&per_page=100", token=token)
        pages = math.ceil(first["total"] / 100)
        for page in range(1, pages + 1):
            body = first if page == 1 else api("GET", f"/items?page={page}&per_page=100", token=token)
            for r in body["items"]:
                con.execute("insert into items values(?,?,?,null)", (r["code"], r["name"], r["stock"]))
    con.execute("insert or replace into meta values('last_result','ok')")
    con.execute("insert or replace into meta values('last_success_at',?)", (datetime.now().isoformat(),))


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        return

    def out(self, status, body):
        raw = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        con = db()
        if self.path in ("/api/items", "/"):
            rows = con.execute("select code, name, stock, price from items order by code").fetchall()
            return self.out(200, [{"code": c, "name": n, "stock": s, "price": p} for c, n, s, p in rows])
        if self.path == "/api/status":
            meta = dict(con.execute("select k, v from meta").fetchall())
            return self.out(200, {"last_result": meta.get("last_result"), "last_success_at": meta.get("last_success_at")})
        self.out(404, {})

    def do_POST(self):
        try:
            sync()
            self.out(200, {"result": "ok"})
        except Exception as e:
            self.out(500, {"error": str(e)})

    def do_PUT(self):
        code = self.path.split("/")[3]
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        db().execute("update items set price = ? where code = ?", (body["price"], code))
        self.out(200, {})


HTTPServer(("127.0.0.1", int(os.environ.get("PORT", "8000"))), H).serve_forever()
