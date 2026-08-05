"""画面とステージに合うBGMをループ再生する。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from importlib.resources import files
from io import BytesIO

import pygame

from earth_invasion.gameplay.stage import GamePhase
from earth_invasion.pygame_app.navigation import AppScreen

ASSET_PACKAGE = "earth_invasion.assets"


class MusicTrack(Enum):
    """再生できるBGM。"""

    TITLE = "title"
    INVASION = "invasion"
    BOSS = "boss"


MUSIC_FILES = {
    MusicTrack.TITLE: "music/bright_title.wav",
    MusicTrack.INVASION: "music/cheerful_invasion.wav",
    MusicTrack.BOSS: "music/defense_boss.wav",
}


@dataclass(slots=True)
class MusicPlayer:
    """BGM専用チャンネルと読み込んだ曲を管理する。"""

    tracks: dict[MusicTrack, pygame.mixer.Sound]
    channel: pygame.mixer.Channel | None
    current_track: MusicTrack | None = None

    @classmethod
    def create(cls, volume: float) -> MusicPlayer:
        """BGMを読み込む。音声を使えない場合は無音で動作する。"""

        _check_volume(volume)
        if pygame.mixer.get_init() is None:
            return cls(tracks={}, channel=None)

        try:
            pygame.mixer.set_reserved(1)
            tracks = {track: _load_music(MUSIC_FILES[track], volume) for track in MusicTrack}
            return cls(tracks=tracks, channel=pygame.mixer.Channel(0))
        except (OSError, pygame.error):
            return cls(tracks={}, channel=None)

    def play(self, track: MusicTrack) -> None:
        """指定したBGMが未再生の場合だけループ再生する。"""

        if track is self.current_track or self.channel is None:
            return

        sound = self.tracks.get(track)
        if sound is None:
            return

        self.channel.play(sound, loops=-1, fade_ms=250)
        self.current_track = track


def music_track_for(screen: AppScreen, phase: GamePhase) -> MusicTrack:
    """現在の画面とステージに合うBGMを返す。"""

    if screen is AppScreen.GAMEPLAY:
        if phase is GamePhase.BOSS:
            return MusicTrack.BOSS
        return MusicTrack.INVASION
    return MusicTrack.TITLE


def _load_music(filename: str, volume: float) -> pygame.mixer.Sound:
    resource = files(ASSET_PACKAGE).joinpath(filename)
    sound = pygame.mixer.Sound(file=BytesIO(resource.read_bytes()))
    sound.set_volume(volume)
    return sound


def _check_volume(volume: float) -> None:
    if volume < 0.0 or volume > 1.0:
        raise ValueError("volumeは0以上1以下にしてください")
