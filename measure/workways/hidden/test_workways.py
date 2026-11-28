"""題材 workways の隠しテスト。

区分（テスト名の頭）:
  test_base_    依頼文に書いてある基本の機能（どのやり方でも通るはず）
  test_way_     今のやり方の決まり W1〜W5 が実装に入ったか。決まりごとに 1 本。主な指標は、通った本数（0〜5）
  test_common_  予約のアプリなら聞くことが多い決まり C1〜C3 が実装に入ったか。決まりごとに 1 本（副の指標）
  test_edge_    決まりの境目。決まりを正確に聞き取って書いたか

決まり（台帳）:
  W1 share    別の車で、時間が重なり、行き先が同じ予約は入れられない（相乗りする）
  W2 short    1 時間より短い予約は入れられない（近くは自転車）
  W3 long     4 時間より長い予約は入れられない（レンタカーを借りる）
  W4 limit    1 人が同時に持てる予約は 2 件まで
  W5 once     同じ人が同じ日に入れられる予約は 1 件だけ
  C1 gap      同じ車の予約は、前の予約の終了から 30 分空ける
  C2 hours    使えるのは 8:00〜19:00
  C3 horizon  予約できるのは今日から 14 日後まで

どのテストも、ほかの決まりに触れない予約だけを使う（日付は明日から 13 日後まで、時刻は 9:00〜17:00、長さは 1〜4 時間、
1 人 2 件まで、同じ人は 1 日 1 件、同じ車のあいだは 30 分以上、行き先は予約ごとに別）。
"""

import datetime

import pytest

pytestmark = pytest.mark.stage1


def d(offset: int) -> str:
    return (datetime.date.today() + datetime.timedelta(days=offset)).isoformat()


# ---- 基本の機能 ----

def test_base_root_returns_200(api):
    assert api.call("GET", "/")[0] == 200


def test_base_register_and_list_cars(api):
    assert api.car("2", "2 号車") == 201
    assert api.car("1", "1 号車") == 201
    status, cars = api.json("GET", "/api/cars")
    assert status == 200
    assert [(c["code"], c["name"]) for c in cars] == [("1", "1 号車"), ("2", "2 号車")]


def test_base_duplicate_car_is_409(api):
    assert api.car("1") == 201
    assert api.car("1", "別の車") == 409


def test_base_reserve_and_list(api):
    api.car("1")
    status, res = api.book("1", d(2), "10:00", "12:00", "佐藤", "山田商会")
    assert status == 201
    assert res.get("id") not in (None, "")
    rows = api.day(d(2))
    assert len(rows) == 1
    r = rows[0]
    assert (r["car"], r["date"], r["start"], r["end"], r["person"], r["destination"]) == ("1", d(2), "10:00", "12:00", "佐藤", "山田商会")
    assert str(r["id"]) == str(res["id"])
    assert api.day(d(3)) == []


def test_base_overlap_on_same_car_is_409(api):
    api.car("1")
    assert api.book("1", d(2), "10:00", "12:00", "佐藤")[0] == 201
    assert api.book("1", d(2), "11:00", "13:00", "鈴木")[0] == 409
    assert api.book("1", d(2), "09:00", "13:00", "高橋")[0] == 409
    assert api.book("1", d(2), "10:30", "11:30", "田中")[0] == 409
    assert len(api.day(d(2))) == 1


def test_base_other_car_and_other_time_are_accepted(api):
    api.car("1")
    api.car("2")
    assert api.book("1", d(2), "10:00", "12:00", "佐藤")[0] == 201
    assert api.book("2", d(2), "10:00", "12:00", "鈴木")[0] == 201
    assert api.book("1", d(2), "14:00", "16:00", "高橋")[0] == 201
    assert api.book("1", d(3), "10:00", "12:00", "田中")[0] == 201
    assert len(api.day(d(2))) == 3


def test_base_list_is_sorted(api):
    api.car("1")
    api.car("2")
    assert api.book("2", d(2), "14:00", "15:00", "佐藤")[0] == 201
    assert api.book("2", d(2), "09:00", "10:00", "鈴木")[0] == 201
    assert api.book("1", d(2), "14:00", "15:00", "高橋")[0] == 201
    assert [(r["start"], r["car"]) for r in api.day(d(2))] == [("09:00", "2"), ("14:00", "1"), ("14:00", "2")]


def test_base_cancel(api):
    api.car("1")
    status, res = api.book("1", d(2), "10:00", "12:00", "佐藤")
    assert status == 201
    assert api.call("DELETE", f"/api/reservations/{res['id']}")[0] in (200, 204)
    assert api.day(d(2)) == []
    assert api.book("1", d(2), "10:00", "12:00", "鈴木")[0] == 201


def test_base_cancel_missing_is_404(api):
    assert api.call("DELETE", "/api/reservations/999999")[0] == 404


def test_base_invalid_reservation_is_400(api):
    api.car("1")
    assert api.book("9", d(2), "10:00", "12:00", "佐藤")[0] == 400
    assert api.book("1", d(2), "12:00", "10:00", "佐藤")[0] == 400
    assert api.book("1", d(2), "10:00", "10:00", "佐藤")[0] == 400
    assert api.book("1", "あした", "10:00", "12:00", "佐藤")[0] == 400
    assert api.day(d(2)) == []


# ---- 今のやり方の決まり（主な指標。決まりごとに 1 本） ----

def test_way_share(api):
    """W1: 別の車で、時間が重なり、行き先が同じ予約は入れられない。"""
    api.car("1")
    api.car("2")
    api.car("3")
    assert api.accepted("1", d(3), "10:00", "12:00", "佐藤", "山田商会")
    assert not api.accepted("2", d(3), "11:00", "13:00", "鈴木", "山田商会"), "重なる時間に同じ行き先の予約が別の車で入った"
    assert api.accepted("2", d(3), "11:00", "13:00", "高橋", "川口工業"), "行き先が違う予約が入らない"
    assert api.accepted("3", d(3), "14:00", "16:00", "田中", "山田商会"), "時間が重ならない同じ行き先の予約が入らない"


def test_way_short(api):
    """W2: 1 時間より短い予約は入れられない。"""
    api.car("1")
    assert not api.accepted("1", d(3), "10:00", "10:20", "佐藤"), "20 分の予約が入った"
    assert not api.accepted("1", d(3), "10:00", "10:45", "佐藤"), "45 分の予約が入った"
    assert api.accepted("1", d(3), "10:00", "11:30", "佐藤"), "1 時間半の予約が入らない"


def test_way_long(api):
    """W3: 4 時間より長い予約は入れられない。"""
    api.car("1")
    assert not api.accepted("1", d(3), "09:00", "17:00", "佐藤"), "8 時間の予約が入った"
    assert not api.accepted("1", d(3), "09:00", "14:00", "佐藤"), "5 時間の予約が入った"
    assert api.accepted("1", d(3), "09:00", "12:00", "佐藤"), "3 時間の予約が入らない"


def test_way_limit(api):
    """W4: 1 人が同時に持てる予約は 2 件まで。"""
    api.car("1")
    assert api.accepted("1", d(2), "10:00", "12:00", "佐藤")
    assert api.accepted("1", d(3), "10:00", "12:00", "佐藤")
    assert not api.accepted("1", d(4), "10:00", "12:00", "佐藤"), "同じ人の 3 件目の予約が入った"
    assert api.accepted("1", d(4), "14:00", "16:00", "鈴木"), "別の人の予約が入らない"
    first = [r for r in api.day(d(2)) if r["person"] == "佐藤"][0]
    assert api.call("DELETE", f"/api/reservations/{first['id']}")[0] in (200, 204)
    assert api.accepted("1", d(5), "10:00", "12:00", "佐藤"), "1 件取り消したあとの予約が入らない"


def test_way_once(api):
    """W5: 同じ人が同じ日に入れられる予約は 1 件だけ。"""
    api.car("1")
    api.car("2")
    assert api.accepted("1", d(5), "09:00", "11:00", "佐藤")
    assert not api.accepted("2", d(5), "14:00", "16:00", "佐藤"), "同じ人の同じ日の 2 件目（別の車、重ならない時間）が入った"
    assert not api.accepted("1", d(5), "14:00", "16:00", "佐藤"), "同じ人の同じ日の 2 件目（同じ車、重ならない時間）が入った"
    assert api.accepted("2", d(5), "14:00", "16:00", "鈴木"), "別の人の予約が入らない"
    assert api.accepted("2", d(6), "14:00", "16:00", "佐藤"), "同じ人の別の日の予約が入らない"


# ---- 予約のアプリなら聞くことが多い決まり（副の指標） ----

def test_common_gap(api):
    """C1: 同じ車の予約は、前の予約の終了から 30 分空ける。"""
    api.car("1")
    assert api.accepted("1", d(3), "11:00", "12:00", "佐藤")
    assert not api.accepted("1", d(3), "12:00", "13:00", "鈴木"), "前の予約の終了と同じ時刻に始まる予約が入った"
    assert not api.accepted("1", d(3), "12:10", "13:30", "鈴木"), "前の予約の終了から 10 分後に始まる予約が入った"
    assert not api.accepted("1", d(3), "09:30", "10:50", "高橋"), "次の予約の開始の 10 分前に終わる予約が入った"
    assert api.accepted("1", d(3), "13:00", "14:00", "田中"), "1 時間空けた予約が入らない"


def test_common_hours(api):
    """C2: 使えるのは 8:00〜19:00。"""
    api.car("1")
    assert not api.accepted("1", d(3), "06:00", "07:30", "佐藤"), "8:00 より前の予約が入った"
    assert not api.accepted("1", d(3), "07:00", "09:00", "鈴木"), "8:00 より前に始まる予約が入った"
    assert not api.accepted("1", d(3), "18:00", "20:00", "高橋"), "19:00 より後に終わる予約が入った"
    assert not api.accepted("1", d(3), "20:00", "21:30", "田中"), "19:00 より後の予約が入った"
    assert api.accepted("1", d(3), "09:00", "12:00", "伊藤"), "9:00〜12:00 の予約が入らない"


def test_common_horizon(api):
    """C3: 予約できるのは今日から 14 日後まで。"""
    api.car("1")
    assert not api.accepted("1", d(20), "10:00", "12:00", "佐藤"), "20 日後の予約が入った"
    assert not api.accepted("1", d(40), "10:00", "12:00", "佐藤"), "40 日後の予約が入った"
    assert api.accepted("1", d(13), "10:00", "12:00", "佐藤"), "13 日後の予約が入らない"


# ---- 決まりの境目 ----

def test_edge_share_same_car_and_touching_times(api):
    api.car("1")
    api.car("2")
    assert api.accepted("1", d(3), "10:00", "12:00", "佐藤", "山田商会")
    assert not api.accepted("2", d(3), "11:00", "13:00", "鈴木", "山田商会")
    assert api.accepted("2", d(3), "12:00", "13:00", "鈴木", "山田商会"), "時刻が接するだけの同じ行き先の予約が入らない"


def test_edge_short_exactly_1_hour(api):
    api.car("1")
    assert not api.accepted("1", d(3), "10:00", "10:59", "佐藤")
    assert api.accepted("1", d(3), "10:00", "11:00", "佐藤")


def test_edge_long_exactly_4_hours(api):
    api.car("1")
    assert not api.accepted("1", d(3), "09:00", "13:01", "佐藤")
    assert api.accepted("1", d(3), "09:00", "13:00", "佐藤")


def test_edge_once_is_per_person_and_day(api):
    api.car("1")
    api.car("2")
    assert api.accepted("1", d(5), "09:00", "11:00", "佐藤")
    assert not api.accepted("2", d(5), "09:00", "11:00", "佐藤")
    assert api.accepted("2", d(5), "09:00", "11:00", "鈴木")
    assert api.accepted("2", d(6), "09:00", "11:00", "佐藤")


def test_edge_gap_exactly_30_minutes(api):
    api.car("1")
    assert api.accepted("1", d(3), "11:00", "12:00", "佐藤")
    assert not api.accepted("1", d(3), "12:29", "13:30", "鈴木")
    assert api.accepted("1", d(3), "12:30", "13:30", "鈴木")
    assert not api.accepted("1", d(3), "09:00", "10:31", "高橋")
    assert api.accepted("1", d(3), "09:00", "10:30", "高橋")


def test_edge_horizon_14_and_15_days(api):
    api.car("1")
    assert not api.accepted("1", d(15), "10:00", "12:00", "佐藤")
    assert api.accepted("1", d(14), "10:00", "12:00", "佐藤")


def test_edge_hours_exactly_8_and_19(api):
    api.car("1")
    api.car("2")
    assert not api.accepted("1", d(3), "07:59", "09:00", "佐藤")
    assert api.accepted("1", d(3), "08:00", "09:00", "佐藤")
    assert not api.accepted("2", d(3), "18:00", "19:01", "鈴木")
    assert api.accepted("2", d(3), "18:00", "19:00", "鈴木")
