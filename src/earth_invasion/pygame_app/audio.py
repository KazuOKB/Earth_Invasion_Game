"""ゲームの出来事を短い効果音として再生する。"""

from __future__ import annotations

import math
from array import array
from dataclasses import dataclass
from enum import Enum

import pygame

from earth_invasion.gameplay.events import GameplayEvents, PlayerHitSource

SAMPLE_RATE = 44_100


class SoundEffect(Enum):
    """ゲーム内で使う効果音。"""

    BEAM = "beam"
    ENEMY_DESTROYED = "enemy_destroyed"
    BOSS_HIT = "boss_hit"
    PLAYER_HIT = "player_hit"
    ENEMY_ATTACK_HIT = "enemy_attack_hit"


@dataclass(slots=True)
class AudioPlayer:
    """利用できる効果音を保持して再生する。"""

    sounds: dict[SoundEffect, pygame.mixer.Sound]
    volume: float

    @classmethod
    def create(cls, volume: float = 1.0) -> AudioPlayer:
        """音声を初期化する。失敗した場合は無音で動作する。"""

        _check_volume(volume)
        player = cls(sounds={}, volume=volume)
        if volume == 0.0:
            return player

        player._enable()
        return player

    def _enable(self) -> None:
        """効果音を使える状態にする。"""

        try:
            if not initialize_audio_mixer():
                return

            self.sounds = {
                SoundEffect.BEAM: _create_tone(760.0, 0.07, 0.16),
                SoundEffect.ENEMY_DESTROYED: _create_tone(180.0, 0.12, 0.25),
                SoundEffect.BOSS_HIT: _create_tone(300.0, 0.08, 0.20),
                SoundEffect.PLAYER_HIT: _create_tone(95.0, 0.18, 0.30),
                SoundEffect.ENEMY_ATTACK_HIT: _create_tone(520.0, 0.16, 0.32),
            }
            for sound in self.sounds.values():
                sound.set_volume(self.volume)
        except (pygame.error, RuntimeError):
            self.sounds = {}

    def play(self, events: GameplayEvents) -> None:
        """今回起きた出来事に対応する効果音を再生する。"""

        for effect in sound_effects_for(events):
            self._play(effect)

    def _play(self, effect: SoundEffect) -> None:
        sound = self.sounds.get(effect)
        if sound is not None:
            sound.play()

    def set_volume(self, volume: float) -> None:
        """すべての効果音へ新しい音量を反映する。"""

        _check_volume(volume)
        self.volume = volume
        if volume > 0.0 and not self.sounds:
            self._enable()
        for sound in self.sounds.values():
            sound.set_volume(volume)

    def play_preview(self) -> None:
        """タイトル画面で効果音の音量を確認する。"""

        self._play(SoundEffect.BEAM)


def sound_effects_for(events: GameplayEvents) -> tuple[SoundEffect, ...]:
    """ゲームの出来事に対応する効果音を順番に返す。"""

    effects: list[SoundEffect] = []
    if events.beam_fired:
        effects.append(SoundEffect.BEAM)
    if events.enemies_destroyed > 0:
        effects.append(SoundEffect.ENEMY_DESTROYED)
    if events.boss_hit_count > 0:
        effects.append(SoundEffect.BOSS_HIT)
    if events.player_hit_source is PlayerHitSource.ENEMY_PROJECTILE:
        effects.append(SoundEffect.ENEMY_ATTACK_HIT)
    elif events.player_hit_source is PlayerHitSource.CONTACT:
        effects.append(SoundEffect.PLAYER_HIT)
    return tuple(effects)


def _create_tone(
    frequency_hz: float,
    duration_seconds: float,
    volume: float,
) -> pygame.mixer.Sound:
    sample_count = round(SAMPLE_RATE * duration_seconds)
    samples = array("h")

    for index in range(sample_count):
        elapsed_seconds = index / SAMPLE_RATE
        fade = 1.0 - index / sample_count
        wave = math.sin(2.0 * math.pi * frequency_hz * elapsed_seconds)
        samples.append(round(32_767 * volume * fade * wave))

    return pygame.mixer.Sound(buffer=samples)


def initialize_audio_mixer() -> bool:
    """必要な場合だけミキサーを初期化する。"""

    try:
        if pygame.mixer.get_init() is None:
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
    except (pygame.error, RuntimeError):
        return False
    return True


def _check_volume(volume: float) -> None:
    if volume < 0.0 or volume > 1.0:
        raise ValueError("volumeは0以上1以下にしてください")
