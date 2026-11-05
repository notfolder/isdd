"""Weighted prize draw for the wheel of fortune."""

from typing import Mapping, Sequence


def pick_prize(prizes: Sequence[Mapping], roll: float) -> Mapping:
    """Return the prize chosen by a weighted draw.

    Each prize is chosen with probability weight / total weight. ``roll`` is a
    uniform random number in the range [0, 1); passing it in keeps the function
    deterministic for tests. Raises ValueError when there are no prizes.
    """
    if not prizes:
        raise ValueError("no prizes to draw from")
    total = sum(int(prize["weight"]) for prize in prizes)
    target = roll * total
    accumulated = 0.0
    for prize in prizes:
        accumulated += int(prize["weight"])
        if target < accumulated:
            return prize
    return prizes[-1]
