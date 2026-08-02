"""固定内部画面とウィンドウ座標の変換テスト。"""

from __future__ import annotations

import pytest

from earth_invasion.pygame_app.display import (
    Viewport,
    calculate_viewport,
    window_to_logical,
)


def test_viewport_uses_entire_window_when_ratio_matches() -> None:
    viewport = calculate_viewport((750, 500), (1500, 1000))

    assert viewport == Viewport(x=0, y=0, width=1500, height=1000)


def test_viewport_centers_horizontal_letterbox() -> None:
    viewport = calculate_viewport((750, 500), (1000, 500))

    assert viewport == Viewport(x=125, y=0, width=750, height=500)


def test_viewport_centers_vertical_letterbox() -> None:
    viewport = calculate_viewport((750, 500), (750, 1000))

    assert viewport == Viewport(x=0, y=250, width=750, height=500)


def test_window_position_converts_to_logical_position() -> None:
    viewport = calculate_viewport((750, 500), (1500, 1000))

    assert window_to_logical((750, 500), viewport, (750, 500)) == (375, 250)


def test_letterbox_position_has_no_logical_position() -> None:
    viewport = calculate_viewport((750, 500), (1000, 500))

    assert window_to_logical((124, 250), viewport, (750, 500)) is None


def test_non_positive_window_size_is_rejected() -> None:
    with pytest.raises(ValueError, match="ウィンドウ"):
        calculate_viewport((750, 500), (0, 500))
