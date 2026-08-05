"""画面とステージに応じたBGM選択を確認する。"""

from __future__ import annotations

import pygame
import pytest

from earth_invasion.gameplay.stage import GamePhase
from earth_invasion.pygame_app.music import MusicPlayer, MusicTrack, music_track_for
from earth_invasion.pygame_app.navigation import AppScreen


@pytest.mark.parametrize(
    "screen",
    [
        AppScreen.TITLE,
        AppScreen.RULES,
        AppScreen.GAME_OVER,
        AppScreen.GAME_CLEAR,
    ],
)
def test_menu_and_result_screens_use_title_music(screen: AppScreen) -> None:
    assert music_track_for(screen, GamePhase.METEOR) is MusicTrack.TITLE


@pytest.mark.parametrize(
    "phase",
    [GamePhase.METEOR, GamePhase.CHASER, GamePhase.SHOOTER],
)
def test_enemy_phases_use_invasion_music(phase: GamePhase) -> None:
    assert music_track_for(AppScreen.GAMEPLAY, phase) is MusicTrack.INVASION


def test_boss_phase_uses_boss_music() -> None:
    assert music_track_for(AppScreen.GAMEPLAY, GamePhase.BOSS) is MusicTrack.BOSS


@pytest.mark.parametrize("volume", [-0.1, 1.1])
def test_invalid_music_volume_is_rejected(volume: float) -> None:
    with pytest.raises(ValueError, match="volume"):
        MusicPlayer.create(volume)


def test_unavailable_audio_device_disables_music(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pygame.mixer, "get_init", lambda: None)

    music_player = MusicPlayer.create(0.3)

    assert music_player.tracks == {}
    assert music_player.channel is None


def test_disabled_music_player_can_update_volume() -> None:
    music_player = MusicPlayer(tracks={}, channel=None, volume=0.0)

    music_player.set_volume(0.6)

    assert music_player.volume == 0.6
