"""現在のゲーム状態と更新処理。"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from earth_invasion.gameplay.commands import PlayerCommand

PLAYER_START_X = 100.0
BEAM_WIDTH = 24
BEAM_HEIGHT = 6
TIME_EPSILON = 1e-9


@dataclass(slots=True)
class Player:
    """プレイヤーの位置と大きさ。"""

    x: float
    y: float
    width: int
    height: int


@dataclass(slots=True)
class Beam:
    """プレイヤーが発射したビーム。"""

    x: float
    y: float
    width: int = BEAM_WIDTH
    height: int = BEAM_HEIGHT


@dataclass(slots=True)
class Meteor:
    """画面右側から左へ移動する隕石。"""

    x: float
    y: float
    width: int
    height: int
    speed: float


@dataclass(slots=True)
class GameSession:
    """ゲーム状態を保持し、固定時間ずつ更新する。"""

    world_width: int
    world_height: int
    movement_speed: float
    beam_speed: float
    beam_cooldown_seconds: float
    meteor_width: int
    meteor_height: int
    meteor_spawn_interval_seconds: float
    meteor_minimum_speed: float
    meteor_maximum_speed: float
    random_source: random.Random
    player: Player
    beams: list[Beam] = field(default_factory=list)
    meteors: list[Meteor] = field(default_factory=list)
    beam_cooldown_remaining: float = 0.0
    meteor_spawn_remaining: float = 0.0

    @classmethod
    def create(
        cls,
        world_width: int,
        world_height: int,
        player_width: int,
        player_height: int,
        movement_speed: float,
        beam_speed: float,
        beam_cooldown_seconds: float,
        meteor_width: int,
        meteor_height: int,
        meteor_spawn_interval_seconds: float,
        meteor_minimum_speed: float,
        meteor_maximum_speed: float,
        random_source: random.Random,
    ) -> GameSession:
        """プレイヤーを画面左側の上下中央に配置する。"""

        _check_positive(world_width, "world_width")
        _check_positive(world_height, "world_height")
        _check_positive(player_width, "player_width")
        _check_positive(player_height, "player_height")
        _check_positive(movement_speed, "movement_speed")
        _check_positive(beam_speed, "beam_speed")
        _check_positive(beam_cooldown_seconds, "beam_cooldown_seconds")
        _check_positive(meteor_width, "meteor_width")
        _check_positive(meteor_height, "meteor_height")
        _check_positive(meteor_spawn_interval_seconds, "meteor_spawn_interval_seconds")
        _check_positive(meteor_minimum_speed, "meteor_minimum_speed")
        _check_positive(meteor_maximum_speed, "meteor_maximum_speed")

        if meteor_minimum_speed > meteor_maximum_speed:
            raise ValueError("meteor_minimum_speedはmeteor_maximum_speed以下にしてください")

        if player_width > world_width or player_height > world_height:
            raise ValueError("プレイヤーの大きさはゲーム画面以下にしてください")
        if meteor_width > world_width or meteor_height > world_height:
            raise ValueError("隕石の大きさはゲーム画面以下にしてください")

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
            beam_speed=beam_speed,
            beam_cooldown_seconds=beam_cooldown_seconds,
            meteor_width=meteor_width,
            meteor_height=meteor_height,
            meteor_spawn_interval_seconds=meteor_spawn_interval_seconds,
            meteor_minimum_speed=meteor_minimum_speed,
            meteor_maximum_speed=meteor_maximum_speed,
            random_source=random_source,
            player=player,
            meteor_spawn_remaining=meteor_spawn_interval_seconds,
        )

    def update(self, command: PlayerCommand, elapsed_seconds: float) -> None:
        """プレイヤー、ビーム、隕石を固定時間だけ更新する。"""

        _check_positive(elapsed_seconds, "elapsed_seconds")
        self._move_player(command, elapsed_seconds)
        self._move_beams(elapsed_seconds)
        self._update_weapon(command, elapsed_seconds)
        self._move_meteors(elapsed_seconds)
        self._update_meteor_spawning(elapsed_seconds)

    def _move_player(self, command: PlayerCommand, elapsed_seconds: float) -> None:
        movement = command.vertical_direction * self.movement_speed * elapsed_seconds
        maximum_y = self.world_height - self.player.height
        self.player.y = min(max(self.player.y + movement, 0.0), float(maximum_y))

    def _move_beams(self, elapsed_seconds: float) -> None:
        for beam in self.beams:
            beam.x += self.beam_speed * elapsed_seconds

        self.beams = [beam for beam in self.beams if beam.x < self.world_width]

    def _update_weapon(self, command: PlayerCommand, elapsed_seconds: float) -> None:
        self.beam_cooldown_remaining = max(
            0.0,
            self.beam_cooldown_remaining - elapsed_seconds,
        )

        if command.fire_pressed and self.beam_cooldown_remaining <= TIME_EPSILON:
            self._fire_beam()
            self.beam_cooldown_remaining = self.beam_cooldown_seconds

    def _fire_beam(self) -> None:
        self.beams.append(
            Beam(
                x=self.player.x + self.player.width,
                y=self.player.y + (self.player.height - BEAM_HEIGHT) / 2,
            )
        )

    def _move_meteors(self, elapsed_seconds: float) -> None:
        for meteor in self.meteors:
            meteor.x -= meteor.speed * elapsed_seconds

        self.meteors = [meteor for meteor in self.meteors if meteor.x + meteor.width > 0]

    def _update_meteor_spawning(self, elapsed_seconds: float) -> None:
        self.meteor_spawn_remaining -= elapsed_seconds

        while self.meteor_spawn_remaining <= TIME_EPSILON:
            self._spawn_meteor()
            self.meteor_spawn_remaining += self.meteor_spawn_interval_seconds

    def _spawn_meteor(self) -> None:
        maximum_y = self.world_height - self.meteor_height
        self.meteors.append(
            Meteor(
                x=float(self.world_width),
                y=self.random_source.uniform(0.0, float(maximum_y)),
                width=self.meteor_width,
                height=self.meteor_height,
                speed=self.random_source.uniform(
                    self.meteor_minimum_speed,
                    self.meteor_maximum_speed,
                ),
            )
        )


def _check_positive(value: int | float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name}は0より大きくしてください")
