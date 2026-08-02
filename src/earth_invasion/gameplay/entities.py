"""ゲーム内に存在する物体。"""

from __future__ import annotations

from dataclasses import dataclass

BEAM_WIDTH = 24
BEAM_HEIGHT = 6


@dataclass(slots=True)
class Player:
    """プレイヤーの位置と大きさ。"""

    x: float
    y: float
    width: int
    height: int
    health: int
    invincibility_remaining: float = 0.0

    @property
    def is_invincible(self) -> bool:
        """被弾後の無敵時間中か返す。"""

        return self.invincibility_remaining > 0.0

    @property
    def is_defeated(self) -> bool:
        """体力がなくなっているか返す。"""

        return self.health <= 0

    def move_vertical(
        self,
        direction: int,
        speed: float,
        elapsed_seconds: float,
        world_height: int,
    ) -> None:
        """上下へ移動し、画面の中で止まる。"""

        movement = direction * speed * elapsed_seconds
        maximum_y = world_height - self.height
        self.y = min(max(self.y + movement, 0.0), float(maximum_y))

    def update_invincibility(self, elapsed_seconds: float) -> None:
        """無敵時間を減らす。"""

        self.invincibility_remaining = max(
            self.invincibility_remaining - elapsed_seconds,
            0.0,
        )

    def take_damage(self, damage: int, invincibility_seconds: float) -> bool:
        """可能ならダメージを受け、受けた場合はTrueを返す。"""

        if self.is_invincible or self.is_defeated:
            return False

        self.health = max(self.health - damage, 0)
        self.invincibility_remaining = invincibility_seconds
        return True


@dataclass(slots=True)
class Beam:
    """プレイヤーが発射したビーム。"""

    x: float
    y: float
    width: int = BEAM_WIDTH
    height: int = BEAM_HEIGHT

    def move(self, speed: float, elapsed_seconds: float) -> None:
        """右へ移動する。"""

        self.x += speed * elapsed_seconds


@dataclass(slots=True)
class Meteor:
    """画面右側から左へ移動する隕石。"""

    x: float
    y: float
    width: int
    height: int
    speed: float

    def move(self, elapsed_seconds: float) -> None:
        """固有の速度で左へ移動する。"""

        self.x -= self.speed * elapsed_seconds


@dataclass(slots=True)
class Chaser:
    """左へ進みながらプレイヤーを追う敵。"""

    x: float
    y: float
    width: int
    height: int
    horizontal_speed: float
    tracking_speed: float

    def move(
        self,
        elapsed_seconds: float,
        target_center_y: float,
        world_height: int,
    ) -> None:
        """左へ進み、上下は目標の中心へ近づく。"""

        self.x -= self.horizontal_speed * elapsed_seconds

        current_center_y = self.y + self.height / 2
        distance_to_target = target_center_y - current_center_y
        maximum_tracking_distance = self.tracking_speed * elapsed_seconds
        tracking_distance = min(
            max(distance_to_target, -maximum_tracking_distance),
            maximum_tracking_distance,
        )
        maximum_y = world_height - self.height
        self.y = min(max(self.y + tracking_distance, 0.0), float(maximum_y))
