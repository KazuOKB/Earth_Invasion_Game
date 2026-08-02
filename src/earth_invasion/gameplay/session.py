"""現在のゲーム状態と更新処理。"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from earth_invasion.gameplay.commands import PlayerCommand
from earth_invasion.gameplay.entities import BEAM_HEIGHT, Beam, Chaser, Meteor, Player
from earth_invasion.gameplay.geometry import rectangles_overlap
from earth_invasion.gameplay.settings import (
    ChaserSettings,
    InvasionSettings,
    MeteorSettings,
    PlayerSettings,
    WeaponSettings,
)
from earth_invasion.gameplay.stage import GamePhase, StageProgress, StageSchedule

PLAYER_START_X = 100.0
TIME_EPSILON = 1e-9


@dataclass(slots=True)
class GameSession:
    """ゲーム状態を保持し、固定時間ずつ更新する。"""

    world_width: int
    world_height: int
    player_settings: PlayerSettings
    weapon_settings: WeaponSettings
    meteor_settings: MeteorSettings
    chaser_settings: ChaserSettings
    invasion_settings: InvasionSettings
    stage: StageProgress
    random_source: random.Random
    player: Player
    beams: list[Beam] = field(default_factory=list)
    meteors: list[Meteor] = field(default_factory=list)
    chasers: list[Chaser] = field(default_factory=list)
    beam_cooldown_remaining: float = 0.0
    meteor_spawn_remaining: float = 0.0
    chaser_spawn_remaining: float = 0.0
    invasion_gauge: int = 0

    @classmethod
    def create(
        cls,
        *,
        world_width: int,
        world_height: int,
        player_settings: PlayerSettings,
        weapon_settings: WeaponSettings,
        meteor_settings: MeteorSettings,
        chaser_settings: ChaserSettings,
        invasion_settings: InvasionSettings,
        stage_schedule: StageSchedule,
        random_source: random.Random,
    ) -> GameSession:
        """プレイヤーを画面左側の上下中央に配置する。"""

        _check_positive(world_width, "world_width")
        _check_positive(world_height, "world_height")

        if player_settings.width > world_width or player_settings.height > world_height:
            raise ValueError("プレイヤーの大きさはゲーム画面以下にしてください")
        if meteor_settings.width > world_width or meteor_settings.height > world_height:
            raise ValueError("隕石の大きさはゲーム画面以下にしてください")
        if chaser_settings.width > world_width or chaser_settings.height > world_height:
            raise ValueError("追尾敵の大きさはゲーム画面以下にしてください")

        player = Player(
            x=min(PLAYER_START_X, float(world_width - player_settings.width)),
            y=(world_height - player_settings.height) / 2,
            width=player_settings.width,
            height=player_settings.height,
            health=player_settings.max_health,
        )
        return cls(
            world_width=world_width,
            world_height=world_height,
            player_settings=player_settings,
            weapon_settings=weapon_settings,
            meteor_settings=meteor_settings,
            chaser_settings=chaser_settings,
            invasion_settings=invasion_settings,
            stage=StageProgress(schedule=stage_schedule),
            random_source=random_source,
            player=player,
            meteor_spawn_remaining=meteor_settings.spawn_interval_seconds,
            chaser_spawn_remaining=chaser_settings.spawn_interval_seconds,
        )

    def update(self, command: PlayerCommand, elapsed_seconds: float) -> None:
        """プレイヤー、ビーム、敵を固定時間だけ更新する。"""

        _check_positive(elapsed_seconds, "elapsed_seconds")
        self.player.update_invincibility(elapsed_seconds)
        self._move_player(command, elapsed_seconds)
        self._move_beams(elapsed_seconds)
        self._update_weapon(command, elapsed_seconds)
        self._move_meteors(elapsed_seconds)
        self._update_meteor_spawning(elapsed_seconds)
        self._move_chasers(elapsed_seconds)
        self._update_chaser_spawning(elapsed_seconds)
        self._resolve_beam_meteor_collisions()
        self._resolve_beam_chaser_collisions()
        self._resolve_player_enemy_collisions()
        self.stage.update(elapsed_seconds, self.invasion_gauge_is_full)

    @property
    def current_phase(self) -> GamePhase:
        """現在のステージ区間を返す。"""

        return self.stage.phase

    @property
    def invasion_gauge_is_full(self) -> bool:
        """侵略ゲージが上限までたまっているか返す。"""

        return self.invasion_gauge >= self.invasion_settings.target

    @property
    def player_is_defeated(self) -> bool:
        """プレイヤーの体力が0か返す。"""

        return self.player.is_defeated

    def _move_player(self, command: PlayerCommand, elapsed_seconds: float) -> None:
        self.player.move_vertical(
            direction=command.vertical_direction,
            speed=self.player_settings.movement_speed,
            elapsed_seconds=elapsed_seconds,
            world_height=self.world_height,
        )

    def _move_beams(self, elapsed_seconds: float) -> None:
        for beam in self.beams:
            beam.move(self.weapon_settings.beam_speed, elapsed_seconds)

        self.beams = [beam for beam in self.beams if beam.x < self.world_width]

    def _update_weapon(self, command: PlayerCommand, elapsed_seconds: float) -> None:
        self.beam_cooldown_remaining = max(
            0.0,
            self.beam_cooldown_remaining - elapsed_seconds,
        )

        if command.fire_pressed and self.beam_cooldown_remaining <= TIME_EPSILON:
            self._fire_beam()
            self.beam_cooldown_remaining = self.weapon_settings.beam_cooldown_seconds

    def _fire_beam(self) -> None:
        self.beams.append(
            Beam(
                x=self.player.x + self.player.width,
                y=self.player.y + (self.player.height - BEAM_HEIGHT) / 2,
            )
        )

    def _move_meteors(self, elapsed_seconds: float) -> None:
        for meteor in self.meteors:
            meteor.move(elapsed_seconds)

        self.meteors = [meteor for meteor in self.meteors if meteor.x + meteor.width > 0]

    def _update_meteor_spawning(self, elapsed_seconds: float) -> None:
        if self.current_phase not in (GamePhase.METEOR, GamePhase.CHASER):
            return

        self.meteor_spawn_remaining -= elapsed_seconds

        while self.meteor_spawn_remaining <= TIME_EPSILON:
            self._spawn_meteor()
            self.meteor_spawn_remaining += self.meteor_settings.spawn_interval_seconds

    def _spawn_meteor(self) -> None:
        maximum_y = self.world_height - self.meteor_settings.height
        self.meteors.append(
            Meteor(
                x=float(self.world_width),
                y=self.random_source.uniform(0.0, float(maximum_y)),
                width=self.meteor_settings.width,
                height=self.meteor_settings.height,
                speed=self.random_source.uniform(
                    self.meteor_settings.minimum_speed,
                    self.meteor_settings.maximum_speed,
                ),
            )
        )

    def _move_chasers(self, elapsed_seconds: float) -> None:
        player_center_y = self.player.y + self.player.height / 2

        for chaser in self.chasers:
            chaser.move(
                elapsed_seconds=elapsed_seconds,
                target_center_y=player_center_y,
                world_height=self.world_height,
            )

        self.chasers = [chaser for chaser in self.chasers if chaser.x + chaser.width > 0]

    def _update_chaser_spawning(self, elapsed_seconds: float) -> None:
        if self.current_phase is not GamePhase.CHASER:
            return

        self.chaser_spawn_remaining -= elapsed_seconds

        while self.chaser_spawn_remaining <= TIME_EPSILON:
            self._spawn_chaser()
            self.chaser_spawn_remaining += self.chaser_settings.spawn_interval_seconds

    def _spawn_chaser(self) -> None:
        maximum_y = self.world_height - self.chaser_settings.height
        self.chasers.append(
            Chaser(
                x=float(self.world_width),
                y=self.random_source.uniform(0.0, float(maximum_y)),
                width=self.chaser_settings.width,
                height=self.chaser_settings.height,
                horizontal_speed=self.chaser_settings.horizontal_speed,
                tracking_speed=self.chaser_settings.tracking_speed,
            )
        )

    def _resolve_beam_meteor_collisions(self) -> None:
        remaining_beams: list[Beam] = []
        remaining_meteors = list(self.meteors)
        destroyed_meteor_count = 0

        for beam in self.beams:
            hit_index = next(
                (
                    index
                    for index, meteor in enumerate(remaining_meteors)
                    if rectangles_overlap(beam, meteor)
                ),
                None,
            )

            if hit_index is None:
                remaining_beams.append(beam)
                continue

            remaining_meteors.pop(hit_index)
            destroyed_meteor_count += 1

        self.beams = remaining_beams
        self.meteors = remaining_meteors

        gained_points = destroyed_meteor_count * self.invasion_settings.meteor_reward
        self._increase_invasion_gauge(gained_points)

    def _resolve_beam_chaser_collisions(self) -> None:
        remaining_beams: list[Beam] = []
        remaining_chasers = list(self.chasers)
        destroyed_chaser_count = 0

        for beam in self.beams:
            hit_index = next(
                (
                    index
                    for index, chaser in enumerate(remaining_chasers)
                    if rectangles_overlap(beam, chaser)
                ),
                None,
            )

            if hit_index is None:
                remaining_beams.append(beam)
                continue

            remaining_chasers.pop(hit_index)
            destroyed_chaser_count += 1

        self.beams = remaining_beams
        self.chasers = remaining_chasers

        gained_points = destroyed_chaser_count * self.invasion_settings.chaser_reward
        self._increase_invasion_gauge(gained_points)

    def _increase_invasion_gauge(self, points: int) -> None:
        self.invasion_gauge = min(
            self.invasion_gauge + points,
            self.invasion_settings.target,
        )

    def _resolve_player_enemy_collisions(self) -> None:
        meteor_count_before_collision = len(self.meteors)
        chaser_count_before_collision = len(self.chasers)

        self.meteors = [
            meteor for meteor in self.meteors if not rectangles_overlap(self.player, meteor)
        ]
        self.chasers = [
            chaser for chaser in self.chasers if not rectangles_overlap(self.player, chaser)
        ]

        enemy_touched_player = (
            len(self.meteors) < meteor_count_before_collision
            or len(self.chasers) < chaser_count_before_collision
        )
        if enemy_touched_player:
            self.player.take_damage(
                damage=1,
                invincibility_seconds=self.player_settings.invincibility_seconds,
            )


def _check_positive(value: int | float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name}は0より大きくしてください")
