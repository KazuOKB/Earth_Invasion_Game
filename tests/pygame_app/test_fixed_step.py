"""固定更新の回数と時間の持ち越しを確認する。"""

from __future__ import annotations

import pytest

from earth_invasion.pygame_app.fixed_step import FixedTimeStep


def test_one_step_is_returned_for_one_update_interval() -> None:
    fixed_time_step = FixedTimeStep(updates_per_second=60)

    assert fixed_time_step.consume(1 / 60) == 1


def test_two_steps_are_returned_for_a_slow_frame() -> None:
    fixed_time_step = FixedTimeStep(updates_per_second=60)

    assert fixed_time_step.consume(1 / 30) == 2


def test_remaining_time_is_carried_to_the_next_frame() -> None:
    fixed_time_step = FixedTimeStep(updates_per_second=60)

    assert fixed_time_step.consume(1 / 120) == 0
    assert fixed_time_step.consume(1 / 120) == 1


def test_long_frame_is_limited() -> None:
    fixed_time_step = FixedTimeStep(updates_per_second=60)

    assert fixed_time_step.consume(10.0) == 15


def test_negative_elapsed_time_is_rejected() -> None:
    fixed_time_step = FixedTimeStep(updates_per_second=60)

    with pytest.raises(ValueError, match="elapsed_seconds"):
        fixed_time_step.consume(-0.1)
