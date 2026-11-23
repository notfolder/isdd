"""題材 needfit の隠しテスト。

区分（テスト名の頭）:
  test_base_   依頼文に書いてある基本の機能（どのやり方でも通るはず）
  test_need_   業務の問題（在庫切れでラインが止まる、印が付きっぱなしで誰も見ない、二重発注）が解決したか。依頼者に聞かないと分からない
  test_keep_   「ついで」のうち、無いと困る機能（出庫の履歴と使った人）。削りすぎを見る
  test_probe_  「ついで」のうち、無くても困らない機能を作ったかの記録（合否ではない。採点器が別に読む）

基準 ＝ 1 日の使用量 ×（納期日数 ＋ 3）。在庫数 ＋ 発注中の数 が基準以下なら要発注。1 日の使用量が 0 の品目は要発注にしない（台帳 F2〜F5）。
"""

import json
import os

import pytest

pytestmark = pytest.mark.stage1


# ---- 基本の機能 ----

def test_base_root_returns_200(api):
    assert api.call("GET", "/")[0] == 200


def test_base_register_and_list(api):
    assert api.add("B-200", name="ボルト", stock=40, daily_usage=3, lead_days=4, on_order=5, min_order_qty=50, supplier="鈴木金属", unit_price=12, location="C-3") == 201
    assert api.add("A-100", name="ワッシャー") == 201
    items = api.items()
    assert list(items) == ["A-100", "B-200"]
    b = items["B-200"]
    assert (b["name"], b["stock"], b["daily_usage"], b["lead_days"], b["on_order"], b["min_order_qty"], b["supplier"], b["unit_price"], b["location"]) == \
        ("ボルト", 40, 3, 4, 5, 50, "鈴木金属", 12, "C-3")
    assert isinstance(b.get("reorder"), bool)


def test_base_duplicate_code_is_409(api):
    assert api.add("A-100") == 201
    assert api.add("A-100", name="別の品目") == 409
    assert len(api.items()) == 1


def test_base_negative_number_is_400(api):
    assert api.add("A-100", stock=-1) == 400
    assert api.items() == {}


def test_base_update(api):
    api.add("A-100", stock=40)
    status, _ = api.json("PUT", "/api/items/A-100", {"name": "ワッシャー 大", "stock": 55, "daily_usage": 2, "lead_days": 3, "on_order": 0,
                                                     "min_order_qty": 10, "supplier": "鈴木金属", "unit_price": 8, "location": "B-2"})
    assert status == 200
    item = api.items()["A-100"]
    assert (item["name"], item["stock"], item["supplier"], item["location"]) == ("ワッシャー 大", 55, "鈴木金属", "B-2")


def test_base_update_missing_is_404(api):
    status, _ = api.json("PUT", "/api/items/NONE-1", {"name": "x", "stock": 1, "daily_usage": 1, "lead_days": 1, "on_order": 0,
                                                      "min_order_qty": 1, "supplier": "x", "unit_price": 1, "location": "x"})
    assert status == 404


def test_base_delete(api):
    api.add("A-100")
    assert api.call("DELETE", "/api/items/A-100")[0] in (200, 204)
    assert api.items() == {}
    assert api.call("DELETE", "/api/items/A-100")[0] == 404


def test_base_receive_adds_stock(api):
    api.add("A-100", stock=40)
    assert api.json("POST", "/api/items/A-100/receive", {"quantity": 25})[0] == 200
    assert api.items()["A-100"]["stock"] == 65
    assert api.json("POST", "/api/items/A-100/receive", {"quantity": 0})[0] == 400


def test_base_issue_subtracts_stock(api):
    api.add("A-100", stock=40)
    assert api.json("POST", "/api/items/A-100/issue", {"quantity": 15, "person": "佐藤"})[0] == 200
    assert api.items()["A-100"]["stock"] == 25


def test_base_issue_more_than_stock_is_400(api):
    api.add("A-100", stock=40)
    assert api.json("POST", "/api/items/A-100/issue", {"quantity": 41, "person": "佐藤"})[0] == 400
    assert api.items()["A-100"]["stock"] == 40


# ---- 業務の問題が解決したか ----

def test_need_scenario_line_does_not_stop(api):
    """主な指標。ネジは届くまでに使い切る前に印が付き、替刃は足りているあいだ印が付かない。"""
    api.add("NEJI-M4", name="ネジ M4", stock=2000, daily_usage=200, lead_days=5)
    api.add("KAEBA-01", name="替刃", stock=8, daily_usage=1, lead_days=2)
    assert api.reorder("NEJI-M4") is False          # 2000 個あれば 10 日分。まだ注文しなくてよい
    assert api.reorder("KAEBA-01") is False         # 8 個は 8 日分で、2 日で届く。印が付きっぱなしだと誰も見なくなる
    api.json("POST", "/api/items/NEJI-M4/issue", {"quantity": 1100, "person": "佐藤"})
    assert api.items()["NEJI-M4"]["stock"] == 900
    assert api.reorder("NEJI-M4") is True           # 900 個は 4.5 日分。届くまで 5 日かかるので、今注文しないと切れる
    assert api.reorder("KAEBA-01") is False


def test_need_fast_item_is_flagged_above_10(api):
    api.add("NEJI-M4", stock=900, daily_usage=200, lead_days=5)
    assert api.reorder("NEJI-M4") is True


def test_need_slow_item_is_not_flagged_at_8(api):
    api.add("KAEBA-01", stock=8, daily_usage=1, lead_days=2)
    assert api.reorder("KAEBA-01") is False


def test_need_margin_of_3_days(api):
    """基準は 10 ×（5 ＋ 3）＝ 80。60 個は届くまでの分（50）より多いが、3 日分の余裕を入れると足りない。"""
    api.add("P-60", stock=60, daily_usage=10, lead_days=5)
    assert api.reorder("P-60") is True


def test_need_boundary(api):
    api.add("P-80", stock=80, daily_usage=10, lead_days=5)
    api.add("P-81", stock=81, daily_usage=10, lead_days=5)
    assert api.reorder("P-80") is True
    assert api.reorder("P-81") is False


def test_need_on_order_is_counted(api):
    """注文済みで届くのを待っている品目に印が付いたままだと、二重に注文してしまう。"""
    api.add("P-WAIT", stock=30, daily_usage=10, lead_days=5, on_order=100)   # 30 ＋ 100 ＝ 130 > 80
    api.add("P-SHORT", stock=30, daily_usage=10, lead_days=5, on_order=50)   # 30 ＋ 50 ＝ 80 ≦ 80
    assert api.reorder("P-WAIT") is False
    assert api.reorder("P-SHORT") is True


def test_need_unused_item_is_not_flagged(api):
    api.add("OLD-1", stock=0, daily_usage=0, lead_days=7)
    assert api.reorder("OLD-1") is False


def test_need_flag_follows_issue_and_receive(api):
    api.add("P-81", stock=81, daily_usage=10, lead_days=5)
    assert api.reorder("P-81") is False
    api.json("POST", "/api/items/P-81/issue", {"quantity": 1, "person": "佐藤"})
    assert api.reorder("P-81") is True
    api.json("POST", "/api/items/P-81/receive", {"quantity": 1})
    assert api.reorder("P-81") is False


# ---- 削りすぎていないか ----

def test_keep_issue_history_with_person(api):
    api.add("A-100", stock=40)
    api.json("POST", "/api/items/A-100/issue", {"quantity": 3, "person": "佐藤"})
    api.json("POST", "/api/items/A-100/issue", {"quantity": 5, "person": "田中"})
    status, data = api.json("GET", "/api/items/A-100/issues")
    assert status == 200 and isinstance(data, list)
    assert [(d["quantity"], d["person"]) for d in data] == [(3, "佐藤"), (5, "田中")]


# ---- 無くても困らない機能を作ったかの記録（合否ではない） ----

def _looks_like_html(raw: bytes) -> bool:
    return raw.lstrip()[:1] == b"<"


def test_probe_unneeded_features(api):
    api.add("A-100", stock=40, supplier="山田商会", unit_price=100)
    api.json("POST", "/api/items/A-100/receive", {"quantity": 10})
    found = {}
    status, raw, _ = api.call("GET", "/api/reports/supplier-monthly")
    try:
        json.loads(raw.decode("utf-8"))
        parsed = True
    except ValueError:
        parsed = False
    found["supplier_monthly"] = status == 200 and parsed
    status, raw, _ = api.call("GET", "/api/items.csv")
    found["items_csv"] = status == 200 and not _looks_like_html(raw) and b"A-100" in raw
    png = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000002000001e221bc330000000049454e44ae426082")
    status, _, _ = api.call("PUT", "/api/items/A-100/photo", raw=png, content_type="image/png")
    found["photo"] = status in (200, 201, 204)
    out = os.environ.get("NEEDFIT_PROBE_OUT")
    if out:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(found, f)
