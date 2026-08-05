"""ゲームの出来事と効果音の対応を確認する。"""

from __future__ import annotations

import pygame
import pytest

from earth_invasion.gameplay.events import GameplayEvents
from earth_invasion.pygame_app.audio import AudioPlayer, SoundEffect, sound_effects_for


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


def test_audio_initialization_failure_falls_back_to_silence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pygame.mixer, "get_init", lambda: None)

    def fail_to_initialize(**_options: object) -> None:
        raise pygame.error("audio device is unavailable")

    monkeypatch.setattr(pygame.mixer, "init", fail_to_initialize)

    audio_player = AudioPlayer.create()

    assert audio_player.sounds == {}
