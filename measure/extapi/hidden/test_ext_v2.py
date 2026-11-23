"""段 2（API v2 への移行）で足すテスト。段 1 のテストも、v2 の連携先に対して全部回す。"""

import pytest

from conftest import make_items, shown

pytestmark = pytest.mark.stage2


def test_ext_v2_stock_is_available_only(app, supplier):
    """一覧の在庫数は、引き当てできる数（available）。引き当て済みの数（reserved）を足さない。"""
    items = make_items(30, reserved=7)
    supplier.set(items=items)
    app.sync()
    got = shown(app)
    assert got["ZK-00010"][1] == 110, f"在庫数が {got['ZK-00010'][1]}（available は 110、reserved は 7）"
    assert all(got[r["code"]][1] == r["stock"] for r in items)


def test_ext_v2_low_stock_and_discontinued_use_available(app, supplier):
    """在庫が少ない商品（5 個以下は 0）と、在庫が残る廃番の商品は、引き当てできる数（available）で見る。"""
    items = make_items(10, reserved=50, discontinued={7, 8}, stock={2: 4, 3: 6, 7: 0})
    supplier.set(items=items)
    app.sync()
    got = shown(app)
    assert got["ZK-00002"][1] == 0, "available が 4 個（reserved は 50 個）の商品が 0 と出ていない"
    assert got["ZK-00003"][1] == 6
    assert "ZK-00007" not in got, "available が 0 の廃番の商品が一覧に出ている"
    assert "ZK-00008" in got


def test_ext_v2_last_page_without_cursor(app, supplier):
    """ちょうど 50 件と 100 件。最後のページの応答には next_cursor のキーが無い（通知は null と書く）。"""
    for count in (50, 100):
        items = make_items(count, tag="B" if count == 100 else "A")
        supplier.set(items=items)
        app.sync()
        assert len(shown(app)) == count
        assert app.status()["last_result"] == "ok"
