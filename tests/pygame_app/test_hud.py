"""HUDに表示するハートの状態を確認する。"""

import pytest

from earth_invasion.pygame_app.hud import heart_states


def test_full_health_fills_three_hearts() -> None:
    assert heart_states(3, 3) == (True, True, True)


def test_damage_removes_filled_hearts() -> None:
    assert heart_states(2, 3) == (True, True, False)
    assert heart_states(1, 3) == (True, False, False)
    assert heart_states(0, 3) == (False, False, False)


def test_health_is_clamped_to_valid_range() -> None:
    assert heart_states(4, 3) == (True, True, True)
    assert heart_states(-1, 3) == (False, False, False)


def test_non_positive_max_health_is_rejected() -> None:
    with pytest.raises(ValueError, match="max_health"):
        heart_states(0, 0)
