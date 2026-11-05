"""画面が呼ぶ API の処理。HTTP の細部には触れず、状態コードと応答の中身を返す。"""

from typing import Any, Dict, Optional, Tuple

from service.validation import PlayerNameError
from service.wheel import WheelService

SERVER_ERROR_MESSAGE = "Something went wrong. Please try again."


def handle_list_prizes(service: WheelService) -> Tuple[int, Any]:
    """報酬の一覧を返す（GET /api/rewards）。"""
    return 200, service.list_prizes()


def handle_spin(service: WheelService, body: Any) -> Tuple[int, Dict[str, Any]]:
    """本文の player_name で抽選する（POST /api/spin）。規則違反は 400。"""
    raw_name = body.get("player_name") if isinstance(body, dict) else None
    try:
        return 200, service.spin(raw_name)
    except PlayerNameError as error:
        return 400, {"error": str(error)}


def handle_list_records(service: WheelService, raw_name: Optional[str]) -> Tuple[int, Any]:
    """利用者名に一致する当選記録を返す（GET /api/records?player_name=...）。規則違反は 400。"""
    try:
        return 200, service.list_records(raw_name)
    except PlayerNameError as error:
        return 400, {"error": str(error)}
