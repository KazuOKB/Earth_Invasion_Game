"""固定内部画面をウィンドウへ拡大する計算。"""

from __future__ import annotations

from dataclasses import dataclass

Size = tuple[int, int]
Point = tuple[int, int]


@dataclass(frozen=True, slots=True)
class Viewport:
    """ウィンドウ内でゲーム画面を表示する範囲。"""

    x: int
    y: int
    width: int
    height: int

    @property
    def size(self) -> Size:
        return self.width, self.height


def calculate_viewport(logical_size: Size, window_size: Size) -> Viewport:
    """縦横比を維持した最大の表示範囲を返す。"""

    logical_width, logical_height = logical_size
    window_width, window_height = window_size
    _check_size(logical_size, "内部画面")
    _check_size(window_size, "ウィンドウ")

    scale = min(
        window_width / logical_width,
        window_height / logical_height,
    )
    scaled_width = max(1, int(logical_width * scale))
    scaled_height = max(1, int(logical_height * scale))

    return Viewport(
        x=(window_width - scaled_width) // 2,
        y=(window_height - scaled_height) // 2,
        width=scaled_width,
        height=scaled_height,
    )


def window_to_logical(
    position: Point,
    viewport: Viewport,
    logical_size: Size,
) -> Point | None:
    """ウィンドウ座標を内部画面の座標へ変換する。"""

    x, y = position
    inside_x = viewport.x <= x < viewport.x + viewport.width
    inside_y = viewport.y <= y < viewport.y + viewport.height

    if not inside_x or not inside_y:
        return None

    logical_width, logical_height = logical_size
    _check_size(logical_size, "内部画面")

    logical_x = int((x - viewport.x) * logical_width / viewport.width)
    logical_y = int((y - viewport.y) * logical_height / viewport.height)

    return (
        min(logical_x, logical_width - 1),
        min(logical_y, logical_height - 1),
    )


def _check_size(size: Size, name: str) -> None:
    width, height = size
    if width <= 0 or height <= 0:
        raise ValueError(f"{name}の幅と高さは0より大きくしてください")
