"""連携先が止まっているとき・途中で失敗したとき: 前回の内容を保つ。売価は取り込みで消えない。"""

import pytest

from conftest import expected, make_items, run_app, shown

pytestmark = pytest.mark.stage1


def test_ext_outage_keeps_previous_items(app, supplier):
    items = make_items(40)
    supplier.set(items=items)
    app.sync()
    supplier.down()
    app.sync()
    assert shown(app) == expected(items), "連携先が止まっているときに、前回の内容が変わった"
    assert app.top_status() == 200, "連携先が止まっていると画面が開かない"


def test_ext_outage_status_failed_and_last_success_kept(app, supplier):
    supplier.set(items=make_items(10))
    app.sync()
    ok = app.status()
    assert ok["last_result"] == "ok" and ok["last_success_at"]
    supplier.down()
    app.sync()
    failed = app.status()
    assert failed["last_result"] == "failed"
    assert failed["last_success_at"] == ok["last_success_at"], "失敗した取り込みで、最後に成功した日時が変わった"


def test_ext_recovers_after_outage(app, supplier):
    supplier.set(items=make_items(20, tag="A"))
    app.sync()
    supplier.down()
    app.sync()
    newer = make_items(25, tag="B")
    supplier.set(items=newer)
    app.sync()
    assert shown(app) == expected(newer)
    assert app.status()["last_result"] == "ok"


def test_ext_first_sync_failure_shows_empty(app, supplier):
    supplier.set(items=make_items(10))
    supplier.down()
    app.sync()
    assert app.items() == []
    status = app.status()
    assert status["last_result"] == "failed" and status["last_success_at"] is None
    assert app.top_status() == 200


def test_ext_partial_failure_keeps_previous_whole(app, supplier):
    """2 ページ目から連携先が止まる。途中まで取れた分を混ぜず、前回成功したときの内容のままにする。"""
    before = make_items(120, tag="A")
    supplier.set(items=before)
    app.sync()
    supplier.set(items=make_items(90, start=31, tag="B"))
    supplier.fail_after(1)
    app.sync()
    assert shown(app) == expected(before), "途中で失敗した取り込みの中身が、一覧に混ざった（または欠けた）"
    assert app.status()["last_result"] == "failed"


def test_ext_price_survives_resync(app, supplier):
    supplier.set(items=make_items(20, tag="A"))
    app.sync()
    app.set_price("ZK-00007", 1280)
    assert app.by_code()["ZK-00007"]["price"] == 1280
    assert app.by_code()["ZK-00008"]["price"] is None
    changed = make_items(20, tag="B")
    supplier.set(items=changed)
    app.sync()
    row = app.by_code()["ZK-00007"]
    assert row["price"] == 1280, "取り込み直したら売価が消えた（変わった）"
    assert (row["name"], row["stock"]) == expected(changed)["ZK-00007"]


def test_ext_price_survives_failed_sync(app, supplier):
    supplier.set(items=make_items(20))
    app.sync()
    app.set_price("ZK-00002", 350)
    supplier.down()
    app.sync()
    assert app.by_code()["ZK-00002"]["price"] == 350


def test_ext_data_survives_restart(supplier, data_dir):
    """同じ DATA_DIR で起動し直したら、取り込んだ内容と売価が残っている（契約）。"""
    items = make_items(12)
    supplier.set(items=items)
    with run_app(supplier.url, data_dir) as first:
        first.sync()
        first.set_price("ZK-00001", 99)
    supplier.down()
    with run_app(supplier.url, data_dir) as second:
        assert shown(second) == expected(items)
        assert second.by_code()["ZK-00001"]["price"] == 99
        assert second.status()["last_result"] == "ok"
