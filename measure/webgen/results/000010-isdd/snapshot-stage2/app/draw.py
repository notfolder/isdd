"""景品の抽選。"""

import secrets


def draw_prize(prizes):
    """景品の一覧から等しい確率で 1 件を選び、その位置（0 から）を返す。

    一覧が空のときは ValueError を送出する。乱数には secrets を使う。
    """
    if not prizes:
        raise ValueError("No prizes are available")
    return secrets.randbelow(len(prizes))
