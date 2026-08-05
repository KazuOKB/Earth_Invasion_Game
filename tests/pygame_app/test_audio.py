"""ゲームの出来事と効果音の対応を確認する。"""

from __future__ import annotations

from earth_invasion.gameplay.events import GameplayEvents
from earth_invasion.pygame_app.audio import SoundEffect, sound_effects_for


def test_no_event_has_no_sound_effect() -> None:
    assert sound_effects_for(GameplayEvents()) == ()


def test_each_gameplay_event_has_a_sound_effect() -> None:
    events = GameplayEvents(
        beam_fired=True,
        enemies_destroyed=2,
        boss_hit_count=1,
        player_was_hit=True,
    )

    assert sound_effects_for(events) == (
        SoundEffect.BEAM,
        SoundEffect.ENEMY_DESTROYED,
        SoundEffect.BOSS_HIT,
        SoundEffect.PLAYER_HIT,
    )
