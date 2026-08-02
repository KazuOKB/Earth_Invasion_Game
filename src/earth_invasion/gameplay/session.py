"""現在のゲーム状態と更新処理。"""

from __future__ import annotations

from dataclasses import dataclass

from earth_invasion.gameplay.commands import PlayerCommand

PLAYER_START_X = 100.0


@dataclass(slots=True)
class Player:
    """プレイヤーの位置と大きさ。"""

    x: float
    y: float
    width: int
    height: int


@dataclass(slots=True)
class GameSession:
    """ゲーム状態を保持し、固定時間ずつ更新する。"""

    world_width: int
    world_height: int
    movement_speed: float
    player: Player

    @classmethod
    def create(
        cls,
        world_width: int,
        world_height: int,
        player_width: int,
        player_height: int,
        movement_speed: float,
    ) -> GameSession:
        """プレイヤーを画面左側の上下中央に配置する。"""

        _check_positive(world_width, "world_width")
        _check_positive(world_height, "world_height")
        _check_positive(player_width, "player_width")
        _check_positive(player_height, "player_height")
        _check_positive(movement_speed, "movement_speed")

        if player_width > world_width or player_height > world_height:
            raise ValueError("プレイヤーの大きさはゲーム画面以下にしてください")

        player = Player(
            x=min(PLAYER_START_X, float(world_width - player_width)),
            y=(world_height - player_height) / 2,
            width=player_width,
            height=player_height,
        )
        return cls(
            world_width=world_width,
            world_height=world_height,
            movement_speed=movement_speed,
            player=player,
        )

    def update(self, command: PlayerCommand, elapsed_seconds: float) -> None:
        """プレイヤーを固定時間だけ移動する。"""

        _check_positive(elapsed_seconds, "elapsed_seconds")
        movement = command.vertical_direction * self.movement_speed * elapsed_seconds
        maximum_y = self.world_height - self.player.height
        self.player.y = min(max(self.player.y + movement, 0.0), float(maximum_y))


def _check_positive(value: int | float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name}は0より大きくしてください")
