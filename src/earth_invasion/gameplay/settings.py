"""ゲームルールへ渡す設定。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlayerSettings:
    """プレイヤーの大きさ、移動速度、耐久力。"""

    width: int
    height: int
    movement_speed: float
    max_health: int
    invincibility_seconds: float

    def __post_init__(self) -> None:
        _check_positive(self.width, "player.width")
        _check_positive(self.height, "player.height")
        _check_positive(self.movement_speed, "player.movement_speed")
        _check_positive(self.max_health, "player.max_health")
        _check_positive(self.invincibility_seconds, "player.invincibility_seconds")


@dataclass(frozen=True, slots=True)
class WeaponSettings:
    """ビームの速度と発射間隔。"""

    beam_speed: float
    beam_cooldown_seconds: float

    def __post_init__(self) -> None:
        _check_positive(self.beam_speed, "weapon.beam_speed")
        _check_positive(self.beam_cooldown_seconds, "weapon.beam_cooldown_seconds")


@dataclass(frozen=True, slots=True)
class MeteorSettings:
    """隕石の大きさ、出現間隔、速度。"""

    width: int
    height: int
    spawn_interval_seconds: float
    minimum_speed: float
    maximum_speed: float

    def __post_init__(self) -> None:
        _check_positive(self.width, "meteor.width")
        _check_positive(self.height, "meteor.height")
        _check_positive(self.spawn_interval_seconds, "meteor.spawn_interval_seconds")
        _check_positive(self.minimum_speed, "meteor.minimum_speed")
        _check_positive(self.maximum_speed, "meteor.maximum_speed")

        if self.minimum_speed > self.maximum_speed:
            raise ValueError("meteor.minimum_speedはmaximum_speed以下にしてください")


@dataclass(frozen=True, slots=True)
class ChaserSettings:
    """追尾敵の大きさ、出現間隔、移動速度。"""

    width: int
    height: int
    spawn_interval_seconds: float
    horizontal_speed: float
    tracking_speed: float

    def __post_init__(self) -> None:
        _check_positive(self.width, "chaser.width")
        _check_positive(self.height, "chaser.height")
        _check_positive(self.spawn_interval_seconds, "chaser.spawn_interval_seconds")
        _check_positive(self.horizontal_speed, "chaser.horizontal_speed")
        _check_positive(self.tracking_speed, "chaser.tracking_speed")


@dataclass(frozen=True, slots=True)
class InvasionSettings:
    """侵略ゲージの上限と敵ごとの増加量。"""

    target: int
    meteor_reward: int
    chaser_reward: int

    def __post_init__(self) -> None:
        _check_positive(self.target, "invasion.target")
        _check_positive(self.meteor_reward, "invasion.meteor_reward")
        _check_positive(self.chaser_reward, "invasion.chaser_reward")


def _check_positive(value: int | float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name}は0より大きくしてください")
