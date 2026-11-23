"""取り込みの中身: 欠落・重複が無い、連携先の内容に合わせる、廃番と無くなった商品を出さない。"""

import pytest

from conftest import expected, make_items, shown

pytestmark = pytest.mark.stage1


def test_ext_import_small_all_items(app, supplier):
    items = make_items(15)
    supplier.set(items=items)
    app.sync()
    assert shown(app) == expected(items)
    assert app.status()["last_result"] == "ok"


def test_ext_import_two_pages_at_documented_page_size(app, supplier):
    """100 件。説明書の上限（per_page=100）を信じて 1 回で終わりにすると、50 件しか取れない。"""
    items = make_items(100)
    supplier.set(items=items)
    app.sync()
    assert shown(app) == expected(items)


def test_ext_import_many_pages_no_missing(app, supplier):
    """330 件。回数の制限と、取り込みの途中でのトークンの失効をまたぐ。"""
    items = make_items(330)
    supplier.set(items=items)
    app.sync()
    got = shown(app)
    assert len(got) == 330, f"330 件のうち {len(got)} 件しか出ていない"
    assert got == expected(items)


def test_ext_sync_twice_no_duplicates(app, supplier):
    items = make_items(60)
    supplier.set(items=items)
    app.sync()
    app.sync()
    assert len(app.items()) == 60
    assert shown(app) == expected(items)


def test_ext_name_and_stock_follow_supplier(app, supplier):
    supplier.set(items=make_items(30, tag="A"))
    app.sync()
    changed = make_items(30, tag="B")
    supplier.set(items=changed)
    app.sync()
    assert shown(app) == expected(changed)


def test_ext_removed_item_disappears(app, supplier):
    supplier.set(items=make_items(30))
    app.sync()
    fewer = make_items(20)
    supplier.set(items=fewer)
    app.sync()
    assert shown(app) == expected(fewer)


def test_ext_discontinued_with_stock_shown(app, supplier):
    """在庫が残っている廃番の商品は、一覧に出す（売り切りたい）。説明書は「廃番の商品は返さない」と書くが、実物は印を付けて返す。"""
    items = make_items(30, discontinued={3, 11, 30})
    supplier.set(items=items)
    app.sync()
    got = shown(app)
    assert {"ZK-00003", "ZK-00011", "ZK-00030"} <= set(got), "在庫が残っている廃番の商品が一覧に出ていない"
    assert got == expected(items)


def test_ext_discontinued_without_stock_hidden(app, supplier):
    """在庫が 0 の廃番の商品は出さない。廃番でない商品は、在庫が 0 でも出す。"""
    items = make_items(30, discontinued={4, 12}, stock={4: 0, 12: 0, 20: 0})
    supplier.set(items=items)
    app.sync()
    got = shown(app)
    assert not {"ZK-00004", "ZK-00012"} & set(got), "在庫が 0 の廃番の商品が一覧に出ている"
    assert got.get("ZK-00020", (None, None))[1] == 0, "廃番でない在庫 0 の商品が一覧に無い"
    assert got == expected(items)


def test_ext_discontinued_sold_out_later_disappears(app, supplier):
    supplier.set(items=make_items(20, discontinued={5}))
    app.sync()
    assert "ZK-00005" in shown(app)
    later = make_items(20, discontinued={5}, stock={5: 0})
    supplier.set(items=later)
    app.sync()
    assert "ZK-00005" not in shown(app), "在庫が 0 になった廃番の商品が一覧に残っている"
    assert shown(app) == expected(later)


def test_ext_low_stock_shown_as_zero(app, supplier):
    """連携先の在庫数が 5 個以下の商品は、一覧の在庫数を 0 と出す。6 個以上はそのまま。"""
    items = make_items(12, stock={1: 0, 2: 1, 3: 5, 4: 6, 5: 7})
    supplier.set(items=items)
    app.sync()
    got = {code: stock for code, (_, stock) in shown(app).items()}
    assert (got["ZK-00002"], got["ZK-00003"]) == (0, 0), f"在庫 1 個と 5 個の商品が {got['ZK-00002']} と {got['ZK-00003']} と出ている（0 と出す）"
    assert (got["ZK-00001"], got["ZK-00004"], got["ZK-00005"], got["ZK-00006"]) == (0, 6, 7, 106)
