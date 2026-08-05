"""ゲームの出来事と効果音の対応を確認する。"""

from __future__ import annotations

import pygame
import pytest

from earth_invasion.gameplay.events import GameplayEvents, PlayerHitSource
from earth_invasion.pygame_app.audio import AudioPlayer, SoundEffect, sound_effects_for


def test_no_event_has_no_sound_effect() -> None:
    assert sound_effects_for(GameplayEvents()) == ()


def test_each_gameplay_event_has_a_sound_effect() -> None:
    events = GameplayEvents(
        beam_fired=True,
        enemies_destroyed=2,
        boss_hit_count=1,
        player_hit_source=PlayerHitSource.CONTACT,
    )

    assert sound_effects_for(events) == (
        SoundEffect.BEAM,
        SoundEffect.ENEMY_DESTROYED,
        SoundEffect.BOSS_HIT,
        SoundEffect.PLAYER_HIT,
    )


def test_enemy_projectile_hit_has_a_distinct_sound() -> None:
    events = GameplayEvents(player_hit_source=PlayerHitSource.ENEMY_PROJECTILE)

    assert sound_effects_for(events) == (SoundEffect.ENEMY_ATTACK_HIT,)


def test_audio_initialization_failure_falls_back_to_silence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pygame.mixer, "get_init", lambda: None)

    def fail_to_initialize(**_options: object) -> None:
        raise pygame.error("audio device is unavailable")

    monkeypatch.setattr(pygame.mixer, "init", fail_to_initialize)

    audio_player = AudioPlayer.create()

    assert audio_player.sounds == {}
    assert audio_player.volume == 1.0


@pytest.mark.parametrize("volume", [-0.1, 1.1])
def test_invalid_sound_effect_volume_is_rejected(volume: float) -> None:
    with pytest.raises(ValueError, match="volume"):
        AudioPlayer.create(volume)


def test_disabled_audio_player_can_update_volume() -> None:
    audio_player = AudioPlayer(sounds={}, volume=0.0)

    audio_player.set_volume(0.6)

    assert audio_player.volume == 0.6
