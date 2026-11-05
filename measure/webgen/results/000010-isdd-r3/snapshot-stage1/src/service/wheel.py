"""抽選と当選記録の業務。"""

import random
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Sequence

from service.validation import validate_player_name
from store.database import Database
from store.repositories import PrizeRepository, RecordRepository


def choose_segment_by_weight(weights: Sequence[int], rng: Any) -> int:
    """重みの比で区分を 1 つ選び、その位置（0 始まり）を返す。

    0 以上 合計未満の乱数 r を取り、先頭から重みを足していって累計が r を超えた区分を選ぶ。
    """
    total = sum(weights)
    if total <= 0:
        raise ValueError("the sum of the weights must be positive")
    pick = rng.randrange(total)
    cumulative = 0
    for index, weight in enumerate(weights):
        cumulative += weight
        if pick < cumulative:
            return index
    raise ValueError("the random pick was out of range")


class WheelService:
    """景品の一覧、抽選、当選履歴の取り出しを行う。"""

    def __init__(
        self,
        database: Database,
        rng: Optional[Any] = None,
        clock: Optional[Callable[[], datetime]] = None,
    ) -> None:
        self._prizes = PrizeRepository(database)
        self._records = RecordRepository(database)
        self._rng = rng if rng is not None else random.SystemRandom()
        self._clock = clock if clock is not None else datetime.now

    def list_prizes(self) -> List[Dict[str, Any]]:
        """表示順の景品一覧を返す。確率は重みの比を小数 1 桁の % にしたもの。"""
        prizes = self._prizes.list_all()
        total = sum(prize["weight"] for prize in prizes)
        return [
            {
                "id": prize["id"],
                "name": prize["name"],
                "description": prize["description"],
                "weight": prize["weight"],
                "probability_percent": round(prize["weight"] * 100.0 / total, 1) if total else 0.0,
                "is_miss": bool(prize["is_miss"]),
                "position": prize["position"],
            }
            for prize in prizes
        ]

    def spin(self, raw_name: Any) -> Dict[str, Any]:
        """利用者名を検証して抽選する。当選したときだけ当選記録を残す。

        利用者名が規則に合わなければ PlayerNameError を投げ、何も記録しない。
        """
        name = validate_player_name(raw_name)
        prizes = self.list_prizes()
        index = choose_segment_by_weight([prize["weight"] for prize in prizes], self._rng)
        chosen = prizes[index]
        record_id = None
        if not chosen["is_miss"]:
            won_at = self._clock().strftime("%Y-%m-%d %H:%M:%S")
            record_id = self._records.insert(name, chosen["id"], chosen["name"], won_at)
        return {
            "segment_index": index,
            "prize_id": chosen["id"],
            "prize_name": chosen["name"],
            "is_miss": chosen["is_miss"],
            "record_id": record_id,
        }

    def list_records(self, raw_name: Any) -> List[Dict[str, Any]]:
        """利用者名に一致する当選記録を新しい順に返す。規則に合わなければ PlayerNameError を投げる。"""
        name = validate_player_name(raw_name)
        return self._records.find_by_player(name)
