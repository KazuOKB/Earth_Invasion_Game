"""被弾フラッシュの時間管理を確認する。"""

from __future__ import annotations

import pytest

from earth_invasion.pygame_app.effects import DamageFlash


def test_trigger_starts_damage_flash() -> None:
    flash = DamageFlash(duration_seconds=0.2)

    flash.trigger()

    assert flash.is_visible
    assert flash.intensity == 1.0


def test_damage_flash_fades_with_time() -> None:
    flash = DamageFlash(duration_seconds=0.2)
    flash.trigger()

    flash.update(0.05)

    assert flash.intensity == pytest.approx(0.75)


def test_damage_flash_stops_at_zero() -> None:
    flash = DamageFlash(duration_seconds=0.2)
    flash.trigger()

    flash.update(1.0)

    assert not flash.is_visible
    assert flash.intensity == 0.0


def test_reset_hides_damage_flash() -> None:
    flash = DamageFlash()
    flash.trigger()

    flash.reset()

    assert not flash.is_visible


def test_invalid_duration_is_rejected() -> None:
    with pytest.raises(ValueError, match="duration_seconds"):
        DamageFlash(duration_seconds=0.0)


def test_negative_elapsed_time_is_rejected() -> None:
    flash = DamageFlash()

    with pytest.raises(ValueError, match="elapsed_seconds"):
        flash.update(-0.1)
