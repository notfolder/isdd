#!/usr/bin/env python3
"""確かめ用の正しい実装 A（SQLite。取り込みは全件を集めてから 1 つのトランザクションで入れ替える）。REF_API_VERSION=2 で v2。"""
import json
import os
import sqlite3
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

VERSION = os.environ.get("REF_API_VERSION", "1")
BASE = os.environ.get("SUPPLIER_API_URL", "http://127.0.0.1:18080") + f"/v{VERSION}"
DATA = Path(os.environ.get("DATA_DIR", "data"))
DATA.mkdir(parents=True, exist_ok=True)
DB = DATA / "app.db"
_token = {"value": None}


def db():
    con = sqlite3.connect(DB)
    con.execute("create table if not exists items(code text primary key, name text, stock integer)")
    con.execute("create table if not exists prices(code text primary key, price integer)")
    con.execute("create table if not exists meta(k text primary key, v text)")
    return con


def call(method, url, body=None, headers=None):
    req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(), method=method, headers=headers or {})
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.status, json.loads(res.read()), res.headers
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}"), e.headers


def new_token():
    status, body, _ = call("POST", BASE + "/auth/token", {"client_id": os.environ.get("SUPPLIER_CLIENT_ID"), "client_secret": os.environ.get("SUPPLIER_CLIENT_SECRET")})
    if status != 200:
        raise RuntimeError(f"auth {status}")
    _token["value"] = body["access_token"]


def get(path):
    for _ in range(8):
        if not _token["value"]:
            new_token()
        status, body, headers = call("GET", BASE + path, headers={"Authorization": "Bearer " + _token["value"]})
        if status == 200:
            return body
        if status == 401:
            _token["value"] = None
            continue
        if status == 429:
            time.sleep(float(headers.get("Retry-After") or 1) + 0.05)
            continue
        raise RuntimeError(f"supplier {status}")
    raise RuntimeError("too many retries")


def shown(stock):
    return 0 if stock <= 5 else stock


def fetch_all():
    rows = []
    if VERSION == "1":
        page = 1
        while True:
            body = get(f"/items?page={page}&per_page=100")
            rows += [(r["code"], r["name"], shown(r["stock"])) for r in body["items"] if not (r.get("discontinued") and r["stock"] == 0)]
            if not body["items"] or page * body["per_page"] >= body["total"]:
                return rows
            page += 1
    cursor = ""
    while True:
        body = get("/items?limit=50" + (f"&cursor={cursor}" if cursor else ""))
        rows += [(r["code"], r["name"], shown(r["stock"]["available"])) for r in body["items"] if not (r.get("status") == "discontinued" and r["stock"]["available"] == 0)]
        cursor = body.get("next_cursor")
        if not cursor:
            return rows


def sync():
    con = db()
    try:
        rows = fetch_all()
        with con:
            con.execute("delete from items")
            con.executemany("insert into items values(?,?,?)", rows)
            con.execute("insert or replace into meta values('last_result','ok')")
            con.execute("insert or replace into meta values('last_success_at',?)", (datetime.now(timezone.utc).isoformat(),))
        return "ok"
    except Exception:
        with con:
            con.execute("insert or replace into meta values('last_result','failed')")
        return "failed"
    finally:
        con.close()


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        return

    def out(self, status, body, ctype="application/json"):
        raw = body.encode() if isinstance(body, str) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def items(self):
        con = db()
        rows = con.execute("select i.code, i.name, i.stock, p.price from items i left join prices p on p.code = i.code order by i.code").fetchall()
        con.close()
        return [{"code": c, "name": n, "stock": s, "price": p} for c, n, s, p in rows]

    def do_GET(self):
        if self.path == "/api/items":
            return self.out(200, self.items())
        if self.path == "/api/status":
            con = db()
            meta = dict(con.execute("select k, v from meta").fetchall())
            con.close()
            return self.out(200, {"last_result": meta.get("last_result"), "last_success_at": meta.get("last_success_at")})
        if self.path == "/":
            rows = "".join(f"<tr><td>{r['code']}</td><td>{r['name']}</td><td>{r['stock']}</td><td>{'' if r['price'] is None else r['price']}</td></tr>" for r in self.items())
            return self.out(200, f"<html><body><form method=post action=/api/sync><button>最新にする</button></form><table>{rows}</table></body></html>", "text/html")
        self.out(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/api/sync":
            return self.out(200, {"result": sync()})
        self.out(404, {"error": "not found"})

    def do_PUT(self):
        parts = self.path.split("/")
        if len(parts) == 5 and parts[1:3] == ["api", "items"] and parts[4] == "price":
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            con = db()
            with con:
                con.execute("insert or replace into prices values(?,?)", (parts[3], body.get("price")))
            con.close()
            return self.out(200, {"ok": True})
        self.out(404, {"error": "not found"})


ThreadingHTTPServer(("127.0.0.1", int(os.environ.get("PORT", "8000"))), H).serve_forever()
