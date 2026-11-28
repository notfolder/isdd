#!/usr/bin/env python3
"""隠しテストを確かめるための見本の実装（作業フォルダには写さない）。環境変数 MODE で作りを替える。

  correct  決まり W1〜W5 と C1〜C3 を全部入れた実装（正しい実装）
  literal  依頼どおり（同じ車で時間が重なる予約だけを断る）
  common   C1〜C3 だけを入れた実装（予約のアプリなら聞くことが多い決まりだけを聞いた場合）
  flow     今の仕事のやり方を聞いて出る W1・W2・C1・C2 だけを入れた実装
  loose    決まりを全部入れたが、境目を取り違えた実装
"""

import datetime
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MODE = os.environ.get("MODE", "correct")
DATA = Path(os.environ.get("DATA_DIR", "data"))
DATA.mkdir(parents=True, exist_ok=True)
DB = DATA / "db.json"
ALL = {"share", "short", "long", "limit", "once", "gap", "hours", "horizon"}
RULES = {"correct": ALL, "literal": set(), "common": {"gap", "hours", "horizon"}, "flow": {"share", "short", "gap", "hours"}, "loose": ALL}[MODE]
LOOSE = MODE == "loose"


def load():
    return json.loads(DB.read_text(encoding="utf-8")) if DB.exists() else {"cars": {}, "reservations": [], "next_id": 1}


def save(db):
    DB.write_text(json.dumps(db, ensure_ascii=False), encoding="utf-8")


def minutes(text):
    if not isinstance(text, str) or not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", text):
        return None
    return int(text[:2]) * 60 + int(text[3:])


def check(db, r):
    """(ステータス, 理由) を返す。受け付けるなら (201, "")。"""
    if r.get("car") not in db["cars"]:
        return 400, "登録していない車"
    try:
        day = datetime.date.fromisoformat(r.get("date"))
    except (TypeError, ValueError):
        return 400, "日付の形が違う"
    start, end = minutes(r.get("start")), minutes(r.get("end"))
    if start is None or end is None or end <= start:
        return 400, "時刻が違う"
    for key, limit in (("person", 30), ("destination", 50)):
        if not isinstance(r.get(key), str) or not r[key].strip() or len(r[key]) > limit:
            return 400, f"{key} が違う"
    today = datetime.date.today()
    if "hours" in RULES and (start < 8 * 60 or end > 19 * 60 or (LOOSE and end >= 19 * 60)):
        return 409, "使えるのは 8:00〜19:00"
    if "horizon" in RULES and (day - today).days > (13 if LOOSE else 14):
        return 409, "予約できるのは 14 日後まで"
    if "short" in RULES and end - start < (61 if LOOSE else 60):
        return 409, "1 時間より短い予約は入れられない"
    if "long" in RULES and end - start > (239 if LOOSE else 240):
        return 409, "4 時間より長い予約は入れられない"
    gap = (31 if LOOSE else 30) if "gap" in RULES else 0
    for o in db["reservations"]:
        if o["date"] != r["date"]:
            continue
        os_, oe = minutes(o["start"]), minutes(o["end"])
        if o["car"] == r["car"]:
            if start < oe + gap and os_ < end + gap:
                return 409, "同じ車の予約と重なるか、あいだが 30 分より短い"
        elif "share" in RULES and o["destination"].strip() == r["destination"].strip() and (start < oe and os_ < end or LOOSE and start <= oe and os_ <= end):
            return 409, "同じ行き先の予約がある（相乗りする）"
        if "once" in RULES and o["person"] == r["person"]:
            return 409, "同じ人が同じ日に入れられる予約は 1 件だけ"
    if "limit" in RULES:
        held = [o for o in db["reservations"] if o["person"] == r["person"] and o["date"] >= today.isoformat()]
        if len(held) >= 2:
            return 409, "1 人が持てる予約は 2 件まで"
    return 201, ""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, status, body=None):
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else b""
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def body(self):
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode("utf-8"))
            return data if isinstance(data, dict) else None
        except ValueError:
            return None

    def do_GET(self):
        path, _, query = self.path.partition("?")
        db = load()
        if path == "/":
            raw = "<html><body><h1>社用車の予約</h1></body></html>".encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        elif path == "/api/cars":
            self.send(200, [{"code": c, "name": n} for c, n in sorted(db["cars"].items())])
        elif path == "/api/reservations":
            day = dict(p.split("=", 1) for p in query.split("&") if "=" in p).get("date")
            rows = [r for r in db["reservations"] if r["date"] == day]
            self.send(200, sorted(rows, key=lambda r: (r["start"], r["car"])))
        else:
            self.send(404, {"error": "not found"})

    def do_POST(self):
        db, data = load(), self.body()
        if data is None:
            return self.send(400, {"error": "JSON でない"})
        if self.path == "/api/cars":
            code, name = data.get("code"), data.get("name")
            if not isinstance(code, str) or not code or not isinstance(name, str) or not name:
                return self.send(400, {"error": "項目が違う"})
            if code in db["cars"]:
                return self.send(409, {"error": "番号の重複"})
            db["cars"][code] = name
            save(db)
            return self.send(201, {"code": code, "name": name})
        if self.path == "/api/reservations":
            status, reason = check(db, data)
            if status != 201:
                return self.send(status, {"error": reason})
            r = {"id": db["next_id"], **{k: data[k] for k in ("car", "date", "start", "end", "person", "destination")}}
            db["next_id"] += 1
            db["reservations"].append(r)
            save(db)
            return self.send(201, r)
        self.send(404, {"error": "not found"})

    def do_DELETE(self):
        m = re.fullmatch(r"/api/reservations/(\d+)", self.path)
        db = load()
        if not m or not any(r["id"] == int(m.group(1)) for r in db["reservations"]):
            return self.send(404, {"error": "not found"})
        db["reservations"] = [r for r in db["reservations"] if r["id"] != int(m.group(1))]
        save(db)
        self.send(204)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", int(os.environ.get("PORT", "8000"))), Handler).serve_forever()
