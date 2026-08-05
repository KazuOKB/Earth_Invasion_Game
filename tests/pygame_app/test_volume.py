"""タイトル画面の音量調整を確認する。"""

from __future__ import annotations

import pytest

from earth_invasion.pygame_app.volume import (
    VolumeControl,
    VolumeKey,
    VolumeTarget,
)


def test_volume_starts_with_configured_values() -> None:
    control = VolumeControl(music_volume=0.0, sound_effect_volume=0.0)

    _assert_selected(control, VolumeTarget.MUSIC)
    assert control.percentage_for(VolumeTarget.MUSIC) == 0
    assert control.percentage_for(VolumeTarget.SOUND_EFFECTS) == 0


def test_up_and_down_select_volume_target() -> None:
    control = VolumeControl(music_volume=0.0, sound_effect_volume=0.0)

    assert control.handle(VolumeKey.DOWN)
    _assert_selected(control, VolumeTarget.SOUND_EFFECTS)

    assert control.handle(VolumeKey.UP)
    _assert_selected(control, VolumeTarget.MUSIC)


def test_left_and_right_adjust_selected_volume() -> None:
    control = VolumeControl(music_volume=0.5, sound_effect_volume=0.5)

    assert control.handle(VolumeKey.RIGHT)
    assert control.music_volume == 0.6

    control.handle(VolumeKey.DOWN)
    assert control.handle(VolumeKey.LEFT)
    assert control.sound_effect_volume == 0.4


def test_volume_stays_between_zero_and_one() -> None:
    control = VolumeControl(music_volume=0.0, sound_effect_volume=1.0)

    control.handle(VolumeKey.LEFT)
    control.handle(VolumeKey.DOWN)
    control.handle(VolumeKey.RIGHT)

    assert control.music_volume == 0.0
    assert control.sound_effect_volume == 1.0


def test_other_key_is_not_handled() -> None:
    control = VolumeControl(music_volume=0.0, sound_effect_volume=0.0)

    assert not control.handle(VolumeKey.OTHER)


@pytest.mark.parametrize("volume", [-0.1, 1.1])
def test_invalid_initial_volume_is_rejected(volume: float) -> None:
    with pytest.raises(ValueError, match="volume"):
        VolumeControl(music_volume=volume, sound_effect_volume=0.0)


def _assert_selected(control: VolumeControl, expected: VolumeTarget) -> None:
    assert control.selected is expected
