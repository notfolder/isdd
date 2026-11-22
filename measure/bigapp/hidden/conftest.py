"""題材 bigapp の隠しテストの準備。アプリ（MEASURE_APP_DIR）を読み込み、テストごとに新しいデータベースで作る。"""

import datetime
import json
import os
import sys
from pathlib import Path

import pytest

APP_DIR = Path(os.environ["MEASURE_APP_DIR"]).resolve()
sys.path.insert(0, str(APP_DIR))
STAGE = int(os.environ.get("MEASURE_STAGE", "0"))
ADMIN_NO, ADMIN_PASSWORD = "900001", "adminpass"
TODAY = datetime.date(2026, 6, 15)
MANIFEST = json.loads((Path(__file__).parent / "manifest.json").read_text(encoding="utf-8"))
if STAGE >= 4:
    MANIFEST = MANIFEST + [{"slug": "umbrellas", "family": "L", "loan_days": 3, "limit": 1, "active_style": None}]
GRACE = 3 if STAGE >= 1 else 0
HALF_UP = STAGE >= 5


def modules(family):
    return [m for m in MANIFEST if m["family"] == family]


def unit_of(m):
    return 15 if (m["slug"] == "meeting_rooms" and STAGE >= 2) else m["unit"]


class Ctx:
    """担当者でログインしたクライアントと、よく使う操作"""

    def __init__(self, client, monkeypatch):
        self.c = client
        self._mp = monkeypatch
        self._n = 100000

    def today(self, offset=0):
        day = TODAY + datetime.timedelta(days=offset)
        self._mp.setenv("APP_TODAY", day.isoformat())
        return day

    def employee(self, name="社員"):
        self._n += 1
        number = str(self._n)
        r = self.c.post("/employees/new", data={"employee_no": number, "name": f"{name}{number}", "role": "employee", "dept": "営業部"})
        assert r.status_code == 201, r.get_data(as_text=True)[:300]
        return number

    def retire(self, number):
        self.c.post("/employees/retire", data={"employee_no": number})

    def set_status(self, number, status):
        r = self.c.post("/employees/set_status", data={"employee_no": number, "status": status})
        assert r.status_code in (200, 302), r.get_data(as_text=True)[:300]

    def status(self, slug):
        r = self.c.get(f"/{slug}/status.json")
        assert r.status_code == 200, f"{slug}/status.json -> {r.status_code}"
        return r.get_json()

    def audit(self):
        return self.c.get("/audit.json").get_json()["rows"]

    # 貸出
    def item(self, slug, code):
        r = self.c.post(f"/{slug}/items/new", data={"code": code, "name": f"品 {code}"})
        assert r.status_code == 302, f"{slug} items/new -> {r.status_code}"

    def lend(self, slug, code, employee, lent_on=None):
        data = {"item_code": code, "employee_no": employee}
        if lent_on:
            data["lent_on"] = lent_on
        return self.c.post(f"/{slug}/lend", data=data).status_code

    def item_state(self, slug, code):
        return next(i for i in self.status(slug)["items"] if i["code"] == code)

    # 予約
    def room(self, slug, code):
        r = self.c.post(f"/{slug}/rooms/new", data={"code": code, "name": f"部屋 {code}"})
        assert r.status_code == 302, f"{slug} rooms/new -> {r.status_code}"

    def book(self, slug, room, employee, start, end, day=None):
        return self.c.post(f"/{slug}/book", data={"room_code": room, "employee_no": employee, "date": (day or TODAY).isoformat(), "start": start, "end": end}).status_code

    def bookings(self, slug):
        return self.status(slug)["bookings"]

    # 申請
    def apply(self, slug, employee, quantity, unit_price):
        return self.c.post(f"/{slug}/apply", data={"employee_no": employee, "quantity": str(quantity), "unit_price": str(unit_price)}).status_code

    def requests(self, slug):
        return self.status(slug)["requests"]


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_TODAY", TODAY.isoformat())
    from app import create_app

    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "hidden.sqlite3")})
    client = app.test_client()
    r = client.post("/login", data={"employee_no": ADMIN_NO, "password": ADMIN_PASSWORD})
    assert r.status_code == 302, "担当者でログインできない"
    return Ctx(client, monkeypatch)
