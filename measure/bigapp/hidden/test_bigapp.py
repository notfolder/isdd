"""題材 bigapp（総務システム、60 機能）の隠しテスト。機能ごとに同じきまりを確かめる（テスト名の [] の中が機能の slug）。

MEASURE_STAGE がその時点の依頼の番号（0 は元のまま）。きまりは依頼で変わる:
  1 以降: 返却の期限の 3 日後までは期限を過ぎた扱いにしない
  2 以降: 会議室（meeting_rooms）の予約は 15 分単位
  3 以降: 休職中（leave）の社員は貸出・予約・申請の対象にできない
  4 以降: 傘の貸出（umbrellas）がある
  5 以降: 税込みの金額は四捨五入
  6 以降: 期限を過ぎた貸出の件数のまとめ（/overdue-summary.json）がある
"""

import pytest

from conftest import ADMIN_NO, GRACE, HALF_UP, STAGE, TODAY, modules, unit_of

L = modules("L")
B = modules("B")
Q = modules("Q")
ids = lambda ms: [m["slug"] for m in ms]  # noqa: E731


def hhmm(minutes):
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


# ---------------- 貸出 ----------------

@pytest.mark.parametrize("m", L, ids=ids(L))
def test_loan_overdue_boundary(ctx, m):
    """期限 + 猶予の日までは lent、その翌日から overdue"""
    slug = m["slug"]
    e = ctx.employee()
    ctx.item(slug, "A-1")
    assert ctx.lend(slug, "A-1", e) == 302
    due = m["loan_days"]
    ctx.today(due + GRACE)
    state = ctx.item_state(slug, "A-1")
    assert state["status"] == "lent", "期限 + 猶予の日はまだ期限を過ぎた扱いにしない"
    assert state["due_on"] == (TODAY.fromordinal(TODAY.toordinal() + due)).isoformat(), "期限の日付は変えない"
    ctx.today(due + GRACE + 1)
    assert ctx.item_state(slug, "A-1")["status"] == "overdue", "期限 + 猶予の翌日から期限を過ぎた扱い"


L2 = [m for m in L if m["limit"] >= 2]


@pytest.mark.parametrize("m", L2, ids=ids(L2))
def test_loan_blocked_when_overdue(ctx, m):
    """期限を過ぎた扱いの貸出を持つ社員には貸さない。猶予の間は貸せる（上限が 2 件以上の機能で確かめる）"""
    slug = m["slug"]
    e = ctx.employee()
    for code in ("A-1", "A-2"):
        ctx.item(slug, code)
    assert ctx.lend(slug, "A-1", e) == 302
    due = m["loan_days"]
    ctx.today(due + GRACE + 1)
    assert ctx.lend(slug, "A-2", e) == 400, "期限を過ぎた扱いの社員には貸さない"
    assert ctx.item_state(slug, "A-2")["status"] == "free"
    ctx.today(due + GRACE)
    assert ctx.lend(slug, "A-2", e) == 302, "猶予の間は貸せる"
    assert ctx.item_state(slug, "A-2")["borrower"] == e


@pytest.mark.parametrize("m", L, ids=ids(L))
def test_loan_limit(ctx, m):
    slug = m["slug"]
    e, other = ctx.employee(), ctx.employee()
    codes = [f"A-{i}" for i in range(1, m["limit"] + 2)]
    for code in codes:
        ctx.item(slug, code)
    for code in codes[:-1]:
        assert ctx.lend(slug, code, e) == 302
    assert ctx.lend(slug, codes[-1], e) == 400, "上限を超えて貸さない"
    assert ctx.lend(slug, codes[-1], other) == 302


@pytest.mark.parametrize("m", L, ids=ids(L))
def test_loan_target_must_be_in_service(ctx, m):
    slug = m["slug"]
    retired = ctx.employee()
    ctx.retire(retired)
    ctx.item(slug, "A-1")
    assert ctx.lend(slug, "A-1", retired) == 400, "退職した社員には貸さない"
    assert ctx.lend(slug, "A-1", "999999") == 400, "居ない社員には貸さない"
    if STAGE >= 3:
        away = ctx.employee()
        ctx.set_status(away, "leave")
        assert ctx.lend(slug, "A-1", away) == 400, "休職中の社員には貸さない"
        assert ctx.item_state(slug, "A-1")["status"] == "free"
        ctx.set_status(away, "active")
        assert ctx.lend(slug, "A-1", away) == 302, "在籍に戻せば貸せる"


@pytest.mark.parametrize("m", L, ids=ids(L))
def test_loan_is_audited(ctx, m):
    slug = m["slug"]
    e = ctx.employee()
    ctx.item(slug, "A-1")
    assert ctx.lend(slug, "A-1", e) == 302
    assert ctx.c.post(f"/{slug}/return", data={"item_code": "A-1"}).status_code == 302
    actions = [r["action"] for r in ctx.audit() if r["module"] == slug]
    assert actions == ["item_create", "lend", "return"]
    assert ctx.item_state(slug, "A-1")["status"] == "free"


# ---------------- 予約 ----------------

@pytest.mark.parametrize("m", B, ids=ids(B))
def test_booking_unit(ctx, m):
    slug, unit = m["slug"], unit_of(m)
    e = ctx.employee()
    ctx.room(slug, "R-1")
    start = 9 * 60
    off = 5 if unit == 15 else unit // 2
    assert ctx.book(slug, "R-1", e, hhmm(start + off), hhmm(start + off + unit)) == 400, "単位に合わない時刻は取れない"
    assert ctx.book(slug, "R-1", e, hhmm(start), hhmm(start + unit)) == 302, "単位どおりの時刻は取れる"
    assert len(ctx.bookings(slug)) == 1


@pytest.mark.parametrize("m", B, ids=ids(B))
def test_booking_overlap_and_daily_limit(ctx, m):
    slug, unit = m["slug"], unit_of(m)
    a, b = ctx.employee(), ctx.employee()
    ctx.room(slug, "R-1")
    s = 10 * 60
    assert ctx.book(slug, "R-1", a, hhmm(s), hhmm(s + 2 * unit)) == 302
    assert ctx.book(slug, "R-1", b, hhmm(s + unit), hhmm(s + 3 * unit)) == 400, "重なる予約は取れない"
    assert ctx.book(slug, "R-1", b, hhmm(s + 2 * unit), hhmm(s + 3 * unit)) == 302, "前の終了と同じ時刻からは取れる"
    # 1 人が 1 日に取れる上限（別の部屋で数える）
    c = ctx.employee()
    for i in range(m["max_per_day"] + 1):
        ctx.room(slug, f"S-{i}")
    for i in range(m["max_per_day"]):
        assert ctx.book(slug, f"S-{i}", c, "13:00", hhmm(13 * 60 + unit)) == 302
    assert ctx.book(slug, f"S-{m['max_per_day']}", c, "15:00", hhmm(15 * 60 + unit)) == 400, "1 日の上限を超えて取れない"


@pytest.mark.parametrize("m", B, ids=ids(B))
def test_booking_target_must_be_in_service(ctx, m):
    slug, unit = m["slug"], unit_of(m)
    retired = ctx.employee()
    ctx.retire(retired)
    ctx.room(slug, "R-1")
    assert ctx.book(slug, "R-1", retired, "09:00", hhmm(9 * 60 + unit)) == 400, "退職した社員は予約できない"
    if STAGE >= 3:
        away = ctx.employee()
        ctx.set_status(away, "leave")
        assert ctx.book(slug, "R-1", away, "09:00", hhmm(9 * 60 + unit)) == 400, "休職中の社員は予約できない"
        assert ctx.bookings(slug) == []
        ctx.set_status(away, "active")
        assert ctx.book(slug, "R-1", away, "09:00", hhmm(9 * 60 + unit)) == 302, "在籍に戻せば予約できる"


# ---------------- 申請 ----------------

@pytest.mark.parametrize("m", Q, ids=ids(Q))
def test_request_amount(ctx, m):
    """税込みの金額。3 × 333 × 1.1 = 1098.9、1 × 15 × 1.1 = 16.5、1 × 14 × 1.1 = 15.4"""
    slug = m["slug"]
    e = ctx.employee()
    for quantity, price in ((3, 333), (1, 15), (1, 14)):
        assert ctx.apply(slug, e, quantity, price) == 302
    amounts = [r["amount_incl_tax"] for r in ctx.requests(slug)]
    assert amounts == ([1099, 17, 15] if HALF_UP else [1098, 16, 15])


@pytest.mark.parametrize("m", Q, ids=ids(Q))
def test_request_self_approval(ctx, m):
    slug = m["slug"]
    e = ctx.employee()
    assert ctx.apply(slug, ADMIN_NO, 1, 100) == 302
    assert ctx.apply(slug, e, 1, 100) == 302
    own, other = ctx.requests(slug)
    assert ctx.c.post(f"/{slug}/approve", data={"request_id": own["id"]}).status_code == 400, "本人は承認できない"
    assert ctx.c.post(f"/{slug}/approve", data={"request_id": other["id"]}).status_code == 302
    states = [r["state"] for r in ctx.requests(slug)]
    assert states == ["pending", "approved"]
    assert ctx.apply(slug, e, m["max_quantity"] + 1, 100) == 400, "数量の上限を超えて申請できない"


@pytest.mark.parametrize("m", Q, ids=ids(Q))
def test_request_target_must_be_in_service(ctx, m):
    slug = m["slug"]
    retired = ctx.employee()
    ctx.retire(retired)
    assert ctx.apply(slug, retired, 1, 100) == 400, "退職した社員は申請できない"
    if STAGE >= 3:
        away = ctx.employee()
        ctx.set_status(away, "leave")
        assert ctx.apply(slug, away, 1, 100) == 400, "休職中の社員は申請できない"
        assert ctx.requests(slug) == []
        ctx.set_status(away, "active")
        assert ctx.apply(slug, away, 1, 100) == 302, "在籍に戻せば申請できる"


# ---------------- 依頼ごとに足されるもの ----------------

@pytest.mark.skipif(STAGE < 3, reason="依頼 3 から")
def test_leave_status(ctx):
    e = ctx.employee()
    ctx.set_status(e, "leave")
    rows = {r["employee_no"]: r for r in ctx.c.get("/employees.json").get_json()["employees"]}
    assert rows[e]["status"] == "leave"
    assert ctx.c.post("/employees/set_status", data={"employee_no": e, "status": "unknown"}).status_code == 400
    ctx.c.post("/logout")
    assert ctx.c.post("/login", data={"employee_no": e, "password": "password1"}).status_code == 400, "休職中はログインできない"


@pytest.mark.skipif(STAGE < 6, reason="依頼 6 から")
def test_overdue_summary(ctx):
    e1, e2 = ctx.employee(), ctx.employee()
    for slug in ("equipment", "keys", "umbrellas"):
        ctx.item(slug, "A-1")
    ctx.item("equipment", "A-2")
    assert ctx.lend("keys", "A-1", e1) == 302          # 期間 1 日
    assert ctx.lend("umbrellas", "A-1", e1) == 302     # 期間 3 日
    assert ctx.lend("equipment", "A-1", e1) == 302     # 期間 14 日
    assert ctx.lend("equipment", "A-2", e2) == 302
    ctx.today(1 + GRACE + 1)                           # 鍵だけが期限を過ぎた扱い
    summary = ctx.c.get("/overdue-summary.json").get_json()["summary"]
    assert set(summary) == {m["slug"] for m in L}, "貸出の機能をすべて入れる"
    assert summary["keys"] == 1 and summary["umbrellas"] == 0 and summary["equipment"] == 0
    ctx.today(14 + GRACE + 1)
    summary = ctx.c.get("/overdue-summary.json").get_json()["summary"]
    assert (summary["keys"], summary["umbrellas"], summary["equipment"]) == (1, 1, 2)
    assert sum(summary.values()) == 4
    assert ctx.c.get("/overdue-summary/").status_code == 200
