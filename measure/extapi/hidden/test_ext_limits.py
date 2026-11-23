"""連携先の決まり: 回数の制限を守る、トークンの失効から回復する、見るだけでは連携先を呼ばない。"""

import time

import pytest

from conftest import expected, make_items, shown

pytestmark = pytest.mark.stage1


def test_ext_rate_limit_no_early_retry(app, supplier):
    """230 件。429 を受けたら Retry-After を待つ。待たずにやり直した要求が 1 回でもあれば落ちる。"""
    items = make_items(230)
    supplier.set(items=items)
    app.sync()
    assert shown(app) == expected(items)
    stats = supplier.stats()
    assert stats["early_retry"] == 0, f"Retry-After を待たない要求が {stats['early_retry']} 回あった"


def test_ext_token_expiry_across_syncs(app, supplier):
    """取り込みを 4 回続ける。トークンを使い回していても、失効（401）から取り直して続けられる。"""
    for round_no, tag in enumerate(["A", "B", "C", "A"]):
        items = make_items(110, tag=tag)
        supplier.set(items=items)
        app.sync()
        assert shown(app) == expected(items), f"{round_no + 1} 回目の取り込みが反映されていない"
        assert app.status()["last_result"] == "ok"


def test_ext_view_does_not_call_supplier(app, supplier):
    """一覧や画面を見るだけでは、連携先を呼ばない（取り込みの操作をしたときだけ）。"""
    supplier.set(items=make_items(20))
    app.sync()
    time.sleep(1.5)
    before = supplier.stats()
    for _ in range(3):
        app.items()
        app.status()
        app.top_status()
    time.sleep(1.5)
    after = supplier.stats()
    assert (after["data_requests"], after["token_issued"]) == (before["data_requests"], before["token_issued"]), "見るだけで連携先を呼んでいる"
