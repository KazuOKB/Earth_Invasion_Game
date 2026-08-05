"""画面とステージに合うBGMをループ再生する。"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum
from importlib.resources import files
from io import BytesIO

import pygame

from earth_invasion.gameplay.stage import GamePhase
from earth_invasion.pygame_app.audio import initialize_audio_mixer
from earth_invasion.pygame_app.navigation import AppScreen

ASSET_PACKAGE = "earth_invasion.assets"


class MusicTrack(Enum):
    """再生できるBGM。"""

    TITLE = "title"
    INVASION = "invasion"
    BOSS = "boss"


MUSIC_FILES = {
    MusicTrack.TITLE: "music/bright_title.ogg",
    MusicTrack.INVASION: "music/cheerful_invasion.ogg",
    MusicTrack.BOSS: "music/defense_boss.ogg",
}


@dataclass(slots=True)
class MusicPlayer:
    """BGM専用チャンネルと読み込んだ曲を管理する。"""

    tracks: dict[MusicTrack, pygame.mixer.Sound]
    channel: pygame.mixer.Channel | None
    volume: float
    current_track: MusicTrack | None = None

    @classmethod
    def create(cls, volume: float) -> MusicPlayer:
        """BGMを読み込む。音声を使えない場合は無音で動作する。"""

        _check_volume(volume)
        player = cls(tracks={}, channel=None, volume=volume)
        if volume == 0.0:
            return player

        player._enable()
        return player

    def _enable(self) -> None:
        """BGMを使える状態にする。"""

        try:
            if not initialize_audio_mixer():
                return

            pygame.mixer.set_reserved(1)
            self.tracks = {track: _load_music(MUSIC_FILES[track]) for track in MusicTrack}
            self.channel = pygame.mixer.Channel(0)
            self.channel.set_volume(self.volume)
        except (OSError, pygame.error, RuntimeError):
            self.tracks = {}
            self.channel = None

    def play(self, track: MusicTrack) -> None:
        """指定したBGMが未再生の場合だけループ再生する。"""

        if track is self.current_track or self.channel is None:
            return

        sound = self.tracks.get(track)
        if sound is None:
            return

        self.channel.play(sound, loops=-1, fade_ms=250)
        self.current_track = track

    def set_volume(self, volume: float) -> None:
        """再生中のBGMへ新しい音量を反映する。"""

        _check_volume(volume)
        self.volume = volume
        if volume > 0.0 and self.channel is None:
            self._enable()
        if self.channel is not None:
            self.channel.set_volume(volume)


def music_track_for(screen: AppScreen, phase: GamePhase) -> MusicTrack:
    """現在の画面とステージに合うBGMを返す。"""

    if screen is AppScreen.GAMEPLAY:
        if phase is GamePhase.BOSS:
            return MusicTrack.BOSS
        return MusicTrack.INVASION
    return MusicTrack.TITLE


def _load_music(filename: str) -> pygame.mixer.Sound:
    resource = files(ASSET_PACKAGE).joinpath(filename)
    if sys.platform == "emscripten":
        return pygame.mixer.Sound(file=str(resource))

    return pygame.mixer.Sound(file=BytesIO(resource.read_bytes()))


def _check_volume(volume: float) -> None:
    if volume < 0.0 or volume > 1.0:
        raise ValueError("volumeは0以上1以下にしてください")
