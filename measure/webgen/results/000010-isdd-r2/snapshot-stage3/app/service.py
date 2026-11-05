"""業務ロジック: 名前の検証、抽選、景品一覧と当選記録の取得。"""

import random
from typing import Any, Dict, List, Optional

from app.database import Database

NAME_MAX_LENGTH = 30


class RequestError(Exception):
    """利用者に見せるエラー。HTTP の状態番号と文言を持つ。"""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def validate_player_name(raw: Any) -> str:
    """名前を検査し、前後の空白を除いた値を返す。

    空、または 30 文字を超えるときは RequestError（400）を投げる。
    """
    name = raw.strip() if isinstance(raw, str) else ""
    if name == "":
        raise RequestError(400, "Please enter your name.")
    if len(name) > NAME_MAX_LENGTH:
        raise RequestError(400, "Name must be 30 characters or fewer.")
    return name


class SpinService:
    """抽選と、景品・当選記録の取得を行う。乱数の源は差し替えられる（テスト用）。"""

    def __init__(self, database: Database, rng: Optional[random.Random] = None) -> None:
        self._database = database
        self._rng = rng if rng is not None else random.Random()

    def get_prizes(self) -> List[Dict[str, Any]]:
        """全景品を表示順に返す。"""
        return self._database.list_prizes()

    def spin(self, raw_name: Any) -> Dict[str, Any]:
        """名前を検査し、全景品から等しい確率で 1 つを選んで当選記録を残す。

        景品が 0 件のときは RequestError（409）を投げ、抽選も記録もしない。
        """
        name = validate_player_name(raw_name)
        prizes = self._database.list_prizes()
        if not prizes:
            raise RequestError(409, "No rewards are available right now.")
        index = self._rng.randrange(len(prizes))
        prize = prizes[index]
        record = self._database.add_winning_record(name, prize)
        return {
            "prize": prize,
            "prize_index": index,
            "prize_count": len(prizes),
            "record": record,
        }

    def get_winnings(self, raw_name: Any) -> Dict[str, Any]:
        """名前で絞り込んだ当選記録を新しい順に返す。"""
        name = validate_player_name(raw_name)
        return {
            "player_name": name,
            "winnings": self._database.list_winnings_by_name(name),
        }
