"""タイトル画面で変更する音量。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

VOLUME_STEP = 0.1


class VolumeTarget(Enum):
    """調整できる音の種類。"""

    MUSIC = "music"
    SOUND_EFFECTS = "sound_effects"


class VolumeKey(Enum):
    """音量調整に使うキー。"""

    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    OTHER = "other"


@dataclass(slots=True)
class VolumeControl:
    """現在の音量と選択中の項目を管理する。"""

    music_volume: float
    sound_effect_volume: float
    selected: VolumeTarget = VolumeTarget.MUSIC

    def __post_init__(self) -> None:
        _check_volume(self.music_volume)
        _check_volume(self.sound_effect_volume)

    def handle(self, key: VolumeKey) -> bool:
        """キーを反映する。音量操作のキーならTrueを返す。"""

        if key is VolumeKey.UP:
            self.selected = VolumeTarget.MUSIC
            return True
        if key is VolumeKey.DOWN:
            self.selected = VolumeTarget.SOUND_EFFECTS
            return True
        if key is VolumeKey.LEFT:
            self._adjust_selected(-VOLUME_STEP)
            return True
        if key is VolumeKey.RIGHT:
            self._adjust_selected(VOLUME_STEP)
            return True
        return False

    def percentage_for(self, target: VolumeTarget) -> int:
        """指定した音量をパーセントで返す。"""

        volume = self.music_volume if target is VolumeTarget.MUSIC else self.sound_effect_volume
        return round(volume * 100)

    def _adjust_selected(self, amount: float) -> None:
        if self.selected is VolumeTarget.MUSIC:
            self.music_volume = _adjusted_volume(self.music_volume, amount)
        else:
            self.sound_effect_volume = _adjusted_volume(self.sound_effect_volume, amount)


def _adjusted_volume(volume: float, amount: float) -> float:
    return round(min(max(volume + amount, 0.0), 1.0), 1)


def _check_volume(volume: float) -> None:
    if volume < 0.0 or volume > 1.0:
        raise ValueError("volumeは0以上1以下にしてください")
