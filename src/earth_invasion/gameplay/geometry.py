"""Pygameに依存しない矩形の当たり判定。"""

from __future__ import annotations

from typing import Protocol


class RectangleLike(Protocol):
    """位置と大きさを持つオブジェクト。"""

    x: float
    y: float
    width: int
    height: int


def rectangles_overlap(first: RectangleLike, second: RectangleLike) -> bool:
    """2つの矩形が重なっている場合にTrueを返す。"""

    return (
        first.x < second.x + second.width
        and first.x + first.width > second.x
        and first.y < second.y + second.height
        and first.y + first.height > second.y
    )
