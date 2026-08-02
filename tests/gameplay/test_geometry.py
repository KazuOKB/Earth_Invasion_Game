"""矩形の当たり判定を確認する。"""

from dataclasses import dataclass

from earth_invasion.gameplay.geometry import rectangles_overlap


@dataclass
class Rectangle:
    x: float
    y: float
    width: int
    height: int


def test_overlapping_rectangles_collide() -> None:
    first = Rectangle(x=10, y=10, width=20, height=20)
    second = Rectangle(x=25, y=25, width=20, height=20)

    assert rectangles_overlap(first, second) is True


def test_separated_rectangles_do_not_collide() -> None:
    first = Rectangle(x=10, y=10, width=20, height=20)
    second = Rectangle(x=40, y=40, width=20, height=20)

    assert rectangles_overlap(first, second) is False


def test_touching_edges_do_not_collide() -> None:
    first = Rectangle(x=10, y=10, width=20, height=20)
    second = Rectangle(x=30, y=10, width=20, height=20)

    assert rectangles_overlap(first, second) is False
