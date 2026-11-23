#!/usr/bin/env python3
"""隠しテストを確かめるための見本の実装（作業フォルダには写さない）。環境変数 MODE で作りを替える。

  correct    業務の問題を解く判定。「ついで」は出庫の履歴だけ作る（正しい実装）
  literal    依頼どおり（在庫数が 10 以下で印）。「ついで」は 4 つとも作る（依頼どおりの実装）
  overbuilt  正しい判定で、「ついで」を 4 つとも作る（作りすぎた実装）
  cutall     正しい判定で、「ついで」を 1 つも作らない（削りすぎた実装）
"""

import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MODE = os.environ.get("MODE", "correct")
DATA = Path(os.environ.get("DATA_DIR", "data"))
DATA.mkdir(parents=True, exist_ok=True)
DB = DATA / "db.json"
FIELDS_INT = ("stock", "daily_usage", "lead_days", "on_order", "min_order_qty", "unit_price")
FIELDS_STR = {"name": 50, "supplier": 50, "location": 30}
EXTRAS = MODE in ("literal", "overbuilt")
HISTORY = MODE != "cutall"


def load():
    return json.loads(DB.read_text(encoding="utf-8")) if DB.exists() else {"items": {}, "issues": {}, "receipts": [], "photos": {}}


def save(db):
    DB.write_text(json.dumps(db, ensure_ascii=False), encoding="utf-8")


def reorder(item) -> bool:
    if MODE == "literal":
        return item["stock"] <= 10
    if item["daily_usage"] == 0:
        return False
    return item["stock"] + item["on_order"] <= item["daily_usage"] * (item["lead_days"] + 3)


def valid(body, with_code):
    if not isinstance(body, dict):
        return False
    if with_code and not re.fullmatch(r"[A-Za-z0-9-]{1,20}", str(body.get("code", ""))):
        return False
    for f in FIELDS_INT:
        if not isinstance(body.get(f), int) or isinstance(body.get(f), bool) or body[f] < 0:
            return False
    return all(isinstance(body.get(f), str) and 0 < len(body[f]) <= n for f, n in FIELDS_STR.items())


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, status, body=None, ctype="application/json; charset=utf-8"):
        raw = body if isinstance(body, bytes) else (json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else b"")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def body(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        return raw

    def handle_any(self, method):
        db = load()
        path = self.path.split("?")[0]
        raw = self.body()
        try:
            data = json.loads(raw.decode("utf-8")) if raw and not path.endswith("/photo") else None
        except ValueError:
            return self.send(400, {"error": "JSON が読めない"})
        if path == "/" and method == "GET":
            return self.send(200, "<html><body>在庫</body></html>".encode("utf-8"), "text/html; charset=utf-8")
        if path == "/api/items" and method == "GET":
            return self.send(200, [dict(i, reorder=reorder(i)) for _, i in sorted(db["items"].items())])
        if path == "/api/items" and method == "POST":
            if not valid(data, True):
                return self.send(400, {"error": "項目の誤り"})
            if data["code"] in db["items"]:
                return self.send(409, {"error": "品目コードの重複"})
            db["items"][data["code"]] = {k: data[k] for k in ("code", "name") + FIELDS_INT + ("supplier", "location")}
            save(db)
            return self.send(201, db["items"][data["code"]])
        if EXTRAS and path == "/api/items.csv" and method == "GET":
            lines = ["code,name,stock"] + [f"{i['code']},{i['name']},{i['stock']}" for _, i in sorted(db["items"].items())]
            return self.send(200, "\n".join(lines).encode("utf-8"), "text/csv; charset=utf-8")
        if EXTRAS and path == "/api/reports/supplier-monthly" and method == "GET":
            total = {}
            for r in db["receipts"]:
                total[r["supplier"]] = total.get(r["supplier"], 0) + r["amount"]
            return self.send(200, total)
        m = re.fullmatch(r"/api/items/([^/]+)(?:/(receive|issue|issues|photo))?", path)
        if not m:
            return self.send(404, {"error": "無い"})
        code, action = m.group(1), m.group(2)
        item = db["items"].get(code)
        if action == "photo" and not EXTRAS:
            return self.send(404, {"error": "無い"})
        if action == "issues" and not HISTORY:
            return self.send(404, {"error": "無い"})
        if item is None:
            return self.send(404, {"error": "無い品目"})
        if action is None and method == "PUT":
            if not valid(data, False):
                return self.send(400, {"error": "項目の誤り"})
            item.update({k: data[k] for k in ("name",) + FIELDS_INT + ("supplier", "location")})
            save(db)
            return self.send(200, item)
        if action is None and method == "DELETE":
            del db["items"][code]
            save(db)
            return self.send(204)
        if action in ("receive", "issue") and method == "POST":
            q = (data or {}).get("quantity")
            if not isinstance(q, int) or isinstance(q, bool) or q < 1 or (action == "issue" and q > item["stock"]):
                return self.send(400, {"error": "数の誤り"})
            if action == "receive":
                item["stock"] += q
                db["receipts"].append({"supplier": item["supplier"], "amount": q * item["unit_price"]})
            else:
                item["stock"] -= q
                db["issues"].setdefault(code, []).append({"quantity": q, "person": (data or {}).get("person", "")})
            save(db)
            return self.send(200, item)
        if action == "issues" and method == "GET":
            return self.send(200, db["issues"].get(code, []))
        if action == "photo" and method == "PUT":
            db["photos"][code] = True
            save(db)
            return self.send(204)
        if action == "photo" and method == "GET":
            return self.send(200 if db["photos"].get(code) else 404, b"", "image/png")
        return self.send(404, {"error": "無い"})

    def do_GET(self):
        self.handle_any("GET")

    def do_POST(self):
        self.handle_any("POST")

    def do_PUT(self):
        self.handle_any("PUT")

    def do_DELETE(self):
        self.handle_any("DELETE")


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", int(os.environ.get("PORT", "8000"))), Handler).serve_forever()
