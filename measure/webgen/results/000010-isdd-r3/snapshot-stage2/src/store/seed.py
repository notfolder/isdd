"""景品が 0 件のときだけ入れる初期データ。"""

from store.database import Database
from store.repositories import PrizeRepository, RecordRepository

# (名前, 説明, 重み, はずれか 0/1)。表示順は並び順どおり。
SAMPLE_PRIZES = [
    ("10% Off Coupon", "Save 10% on your next order", 15, 0),
    ("Free Coffee", "One free coffee at any store", 10, 0),
    ("Free Shipping", "Free shipping on one order", 10, 0),
    ("$5 Voucher", "A $5 voucher for any purchase", 8, 0),
    ("Mystery Gift", "A surprise gift from our team", 5, 0),
    ("Grand Prize: $50 Gift Card", "A $50 gift card", 2, 0),
    ("Try again", "No prize this time", 50, 1),
]

SAMPLE_PLAYER_NAME = "Sample Player"

# (景品名, 当選日時)。景品名は SAMPLE_PRIZES のものを使う。
SAMPLE_RECORDS = [
    ("Free Coffee", "2026-11-04 18:30:00"),
    ("10% Off Coupon", "2026-11-05 09:15:00"),
]


def seed_sample_data(database: Database) -> bool:
    """景品が 0 件のときだけ初期データを入れる。入れたら True、入れなければ False を返す。"""
    prize_repo = PrizeRepository(database)
    if prize_repo.count() > 0:
        return False
    record_repo = RecordRepository(database)
    prize_ids = {}
    for position, (name, description, weight, is_miss) in enumerate(SAMPLE_PRIZES, start=1):
        prize_ids[name] = prize_repo.insert(name, description, weight, is_miss, position)
    for prize_name, won_at in SAMPLE_RECORDS:
        record_repo.insert(SAMPLE_PLAYER_NAME, prize_ids[prize_name], prize_name, won_at)
    return True
