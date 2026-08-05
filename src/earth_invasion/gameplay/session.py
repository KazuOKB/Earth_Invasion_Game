"""現在のゲーム状態と更新処理。"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from earth_invasion.gameplay.commands import PlayerCommand
from earth_invasion.gameplay.entities import (
    BEAM_HEIGHT,
    ENEMY_PROJECTILE_HEIGHT,
    ENEMY_PROJECTILE_WIDTH,
    Beam,
    Boss,
    Chaser,
    EnemyProjectile,
    Meteor,
    Player,
    Shooter,
)
from earth_invasion.gameplay.events import GameplayEvents, PlayerHitSource
from earth_invasion.gameplay.geometry import rectangles_overlap
from earth_invasion.gameplay.settings import (
    BossSettings,
    ChaserSettings,
    InvasionSettings,
    MeteorSettings,
    PlayerSettings,
    ShooterSettings,
    WeaponSettings,
)
from earth_invasion.gameplay.stage import GamePhase, StageProgress, StageSchedule
from earth_invasion.gameplay.status import GameStatus

PLAYER_START_X = 100.0
BOSS_RIGHT_MARGIN = 40.0
TIME_EPSILON = 1e-9


@dataclass(slots=True)
class GameSession:
    """ゲーム状態を保持し、固定時間ずつ更新する。"""

    world_width: int
    world_height: int
    playfield_top: int
    player_settings: PlayerSettings
    weapon_settings: WeaponSettings
    meteor_settings: MeteorSettings
    chaser_settings: ChaserSettings
    shooter_settings: ShooterSettings
    boss_settings: BossSettings
    invasion_settings: InvasionSettings
    stage: StageProgress
    random_source: random.Random
    player: Player
    status: GameStatus = GameStatus.PLAYING
    beams: list[Beam] = field(default_factory=list)
    meteors: list[Meteor] = field(default_factory=list)
    chasers: list[Chaser] = field(default_factory=list)
    shooters: list[Shooter] = field(default_factory=list)
    boss: Boss | None = None
    enemy_projectiles: list[EnemyProjectile] = field(default_factory=list)
    beam_cooldown_remaining: float = 0.0
    meteor_spawn_remaining: float = 0.0
    chaser_spawn_remaining: float = 0.0
    shooter_spawn_remaining: float = 0.0
    invasion_gauge: int = 0

    @classmethod
    def create(
        cls,
        *,
        world_width: int,
        world_height: int,
        playfield_top: int,
        player_settings: PlayerSettings,
        weapon_settings: WeaponSettings,
        meteor_settings: MeteorSettings,
        chaser_settings: ChaserSettings,
        shooter_settings: ShooterSettings,
        boss_settings: BossSettings,
        invasion_settings: InvasionSettings,
        stage_schedule: StageSchedule,
        random_source: random.Random,
    ) -> GameSession:
        """プレイヤーを画面左側の上下中央に配置する。"""

        _check_positive(world_width, "world_width")
        _check_positive(world_height, "world_height")

        if playfield_top < 0 or playfield_top >= world_height:
            raise ValueError("playfield_topは0以上かつworld_height未満にしてください")

        playfield_height = world_height - playfield_top

        if player_settings.width > world_width or player_settings.height > playfield_height:
            raise ValueError("プレイヤーの大きさはゲーム領域以下にしてください")
        if meteor_settings.width > world_width or meteor_settings.height > playfield_height:
            raise ValueError("隕石の大きさはゲーム領域以下にしてください")
        if chaser_settings.width > world_width or chaser_settings.height > playfield_height:
            raise ValueError("追尾敵の大きさはゲーム領域以下にしてください")
        if shooter_settings.width > world_width or shooter_settings.height > playfield_height:
            raise ValueError("攻撃敵の大きさはゲーム領域以下にしてください")
        if boss_settings.width > world_width or boss_settings.height > playfield_height:
            raise ValueError("ボスの大きさはゲーム領域以下にしてください")

        player = _create_player(world_width, world_height, playfield_top, player_settings)
        return cls(
            world_width=world_width,
            world_height=world_height,
            playfield_top=playfield_top,
            player_settings=player_settings,
            weapon_settings=weapon_settings,
            meteor_settings=meteor_settings,
            chaser_settings=chaser_settings,
            shooter_settings=shooter_settings,
            boss_settings=boss_settings,
            invasion_settings=invasion_settings,
            stage=StageProgress(schedule=stage_schedule),
            random_source=random_source,
            player=player,
            meteor_spawn_remaining=meteor_settings.spawn_interval_seconds,
            chaser_spawn_remaining=chaser_settings.spawn_interval_seconds,
            shooter_spawn_remaining=shooter_settings.spawn_interval_seconds,
        )

    def update(self, command: PlayerCommand, elapsed_seconds: float) -> GameplayEvents:
        """ゲームを固定時間だけ更新し、今回起きた出来事を返す。"""

        _check_positive(elapsed_seconds, "elapsed_seconds")
        if self.status is not GameStatus.PLAYING:
            return GameplayEvents()

        self._start_boss_battle_if_needed()
        self.player.update_invincibility(elapsed_seconds)
        self._move_player(command, elapsed_seconds)
        self._move_beams(elapsed_seconds)
        beam_fired = self._update_weapon(command, elapsed_seconds)
        self._move_meteors(elapsed_seconds)
        self._update_meteor_spawning(elapsed_seconds)
        self._move_chasers(elapsed_seconds)
        self._update_chaser_spawning(elapsed_seconds)
        self._move_shooters(elapsed_seconds)
        self._update_shooter_spawning(elapsed_seconds)
        self._move_boss(elapsed_seconds)
        self._move_enemy_projectiles(elapsed_seconds)
        self._update_shooter_firing(elapsed_seconds)
        self._update_boss_firing(elapsed_seconds)
        enemies_destroyed = self._resolve_beam_meteor_collisions()
        enemies_destroyed += self._resolve_beam_chaser_collisions()
        enemies_destroyed += self._resolve_beam_shooter_collisions()
        boss_hit_count = self._resolve_beam_boss_collisions()

        player_hit_source = None
        if not self.is_game_clear:
            player_hit_source = self._resolve_player_damage_collisions()

        if not self.is_finished:
            self.stage.update(elapsed_seconds, self.invasion_gauge_is_full)
            self._start_boss_battle_if_needed()

        return GameplayEvents(
            beam_fired=beam_fired,
            enemies_destroyed=enemies_destroyed,
            boss_hit_count=boss_hit_count,
            player_hit_source=player_hit_source,
        )

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

    @property
    def is_game_over(self) -> bool:
        """ゲームオーバー状態か返す。"""

        return self.status is GameStatus.GAME_OVER

    @property
    def is_game_clear(self) -> bool:
        """ゲームクリア状態か返す。"""

        return self.status is GameStatus.GAME_CLEAR

    @property
    def is_finished(self) -> bool:
        """ゲームオーバーまたはゲームクリアか返す。"""

        return self.status is not GameStatus.PLAYING

    def restart(self) -> None:
        """すべてのゲーム状態を初期値へ戻す。"""

        self.player = _create_player(
            self.world_width,
            self.world_height,
            self.playfield_top,
            self.player_settings,
        )
        self.stage = StageProgress(schedule=self.stage.schedule)
        self.beams = []
        self.meteors = []
        self.chasers = []
        self.shooters = []
        self.boss = None
        self.enemy_projectiles = []
        self.beam_cooldown_remaining = 0.0
        self.meteor_spawn_remaining = self.meteor_settings.spawn_interval_seconds
        self.chaser_spawn_remaining = self.chaser_settings.spawn_interval_seconds
        self.shooter_spawn_remaining = self.shooter_settings.spawn_interval_seconds
        self.invasion_gauge = 0
        self.status = GameStatus.PLAYING

    def _move_player(self, command: PlayerCommand, elapsed_seconds: float) -> None:
        self.player.move_vertical(
            direction=command.vertical_direction,
            speed=self.player_settings.movement_speed,
            elapsed_seconds=elapsed_seconds,
            world_top=self.playfield_top,
            world_height=self.world_height,
        )

    def _move_beams(self, elapsed_seconds: float) -> None:
        for beam in self.beams:
            beam.move(self.weapon_settings.beam_speed, elapsed_seconds)

        self.beams = [beam for beam in self.beams if beam.x < self.world_width]

    def _update_weapon(self, command: PlayerCommand, elapsed_seconds: float) -> bool:
        self.beam_cooldown_remaining = max(
            0.0,
            self.beam_cooldown_remaining - elapsed_seconds,
        )

        if command.fire_pressed and self.beam_cooldown_remaining <= TIME_EPSILON:
            self._fire_beam()
            self.beam_cooldown_remaining = self.weapon_settings.beam_cooldown_seconds
            return True

        return False

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
                y=self.random_source.uniform(float(self.playfield_top), float(maximum_y)),
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
                world_top=self.playfield_top,
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
                y=self.random_source.uniform(float(self.playfield_top), float(maximum_y)),
                width=self.chaser_settings.width,
                height=self.chaser_settings.height,
                horizontal_speed=self.chaser_settings.horizontal_speed,
                tracking_speed=self.chaser_settings.tracking_speed,
            )
        )

    def _move_shooters(self, elapsed_seconds: float) -> None:
        for shooter in self.shooters:
            shooter.move(elapsed_seconds)

        self.shooters = [shooter for shooter in self.shooters if shooter.x + shooter.width > 0]

    def _update_shooter_spawning(self, elapsed_seconds: float) -> None:
        if self.current_phase is not GamePhase.SHOOTER:
            return

        self.shooter_spawn_remaining -= elapsed_seconds

        while self.shooter_spawn_remaining <= TIME_EPSILON:
            self._spawn_shooter()
            self.shooter_spawn_remaining += self.shooter_settings.spawn_interval_seconds

    def _spawn_shooter(self) -> None:
        maximum_y = self.world_height - self.shooter_settings.height
        self.shooters.append(
            Shooter(
                x=float(self.world_width),
                y=self.random_source.uniform(float(self.playfield_top), float(maximum_y)),
                width=self.shooter_settings.width,
                height=self.shooter_settings.height,
                horizontal_speed=self.shooter_settings.horizontal_speed,
                shot_cooldown_remaining=self.shooter_settings.shot_interval_seconds,
            )
        )

    def _update_shooter_firing(self, elapsed_seconds: float) -> None:
        if self.current_phase is not GamePhase.SHOOTER:
            return

        for shooter in self.shooters:
            shooter.update_shot_cooldown(elapsed_seconds)
            if shooter.shot_cooldown_remaining > TIME_EPSILON:
                continue

            self._fire_enemy_projectile(shooter)
            shooter.shot_cooldown_remaining = self.shooter_settings.shot_interval_seconds

    def _fire_enemy_projectile(self, shooter: Shooter) -> None:
        projectile_x = shooter.x - ENEMY_PROJECTILE_WIDTH
        projectile_y = shooter.y + (shooter.height - ENEMY_PROJECTILE_HEIGHT) / 2
        self._fire_aimed_projectile(
            x=projectile_x,
            y=projectile_y,
            speed=self.shooter_settings.projectile_speed,
        )

    def _start_boss_battle_if_needed(self) -> None:
        if self.current_phase is not GamePhase.BOSS or self.boss is not None:
            return

        self.meteors = []
        self.chasers = []
        self.shooters = []
        self.enemy_projectiles = []
        maximum_x = self.world_width - self.boss_settings.width
        boss_x = max(float(maximum_x) - BOSS_RIGHT_MARGIN, 0.0)
        boss_y = (self.playfield_top + self.world_height - self.boss_settings.height) / 2
        self.boss = Boss(
            x=boss_x,
            y=boss_y,
            width=self.boss_settings.width,
            height=self.boss_settings.height,
            health=self.boss_settings.max_health,
            vertical_speed=self.boss_settings.vertical_speed,
            vertical_direction=1,
            shot_cooldown_remaining=self.boss_settings.shot_interval_seconds,
        )

    def _move_boss(self, elapsed_seconds: float) -> None:
        if self.boss is None:
            return

        self.boss.move(elapsed_seconds, self.playfield_top, self.world_height)

    def _update_boss_firing(self, elapsed_seconds: float) -> None:
        if self.current_phase is not GamePhase.BOSS or self.boss is None:
            return

        self.boss.update_shot_cooldown(elapsed_seconds)
        if self.boss.shot_cooldown_remaining > TIME_EPSILON:
            return

        projectile_x = self.boss.x - ENEMY_PROJECTILE_WIDTH
        projectile_y = self.boss.y + (self.boss.height - ENEMY_PROJECTILE_HEIGHT) / 2
        self._fire_aimed_projectile(
            x=projectile_x,
            y=projectile_y,
            speed=self.boss_settings.projectile_speed,
        )
        self.boss.shot_cooldown_remaining = self.boss_settings.shot_interval_seconds

    def _fire_aimed_projectile(self, *, x: float, y: float, speed: float) -> None:
        projectile_center_x = x + ENEMY_PROJECTILE_WIDTH / 2
        projectile_center_y = y + ENEMY_PROJECTILE_HEIGHT / 2
        player_center_x = self.player.x + self.player.width / 2
        player_center_y = self.player.y + self.player.height / 2
        distance_x = player_center_x - projectile_center_x
        distance_y = player_center_y - projectile_center_y
        distance = math.hypot(distance_x, distance_y)

        if distance <= TIME_EPSILON:
            velocity_x = -speed
            velocity_y = 0.0
        else:
            speed_ratio = speed / distance
            velocity_x = distance_x * speed_ratio
            velocity_y = distance_y * speed_ratio

        self.enemy_projectiles.append(
            EnemyProjectile(
                x=x,
                y=y,
                velocity_x=velocity_x,
                velocity_y=velocity_y,
            )
        )

    def _move_enemy_projectiles(self, elapsed_seconds: float) -> None:
        for projectile in self.enemy_projectiles:
            projectile.move(elapsed_seconds)

        self.enemy_projectiles = [
            projectile
            for projectile in self.enemy_projectiles
            if projectile.x + projectile.width > 0
            and projectile.x < self.world_width
            and projectile.y >= self.playfield_top
            and projectile.y < self.world_height
        ]

    def _resolve_beam_meteor_collisions(self) -> int:
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
        return destroyed_meteor_count

    def _resolve_beam_chaser_collisions(self) -> int:
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
        return destroyed_chaser_count

    def _resolve_beam_shooter_collisions(self) -> int:
        remaining_beams: list[Beam] = []
        remaining_shooters = list(self.shooters)
        destroyed_shooter_count = 0

        for beam in self.beams:
            hit_index = next(
                (
                    index
                    for index, shooter in enumerate(remaining_shooters)
                    if rectangles_overlap(beam, shooter)
                ),
                None,
            )

            if hit_index is None:
                remaining_beams.append(beam)
                continue

            remaining_shooters.pop(hit_index)
            destroyed_shooter_count += 1

        self.beams = remaining_beams
        self.shooters = remaining_shooters

        gained_points = destroyed_shooter_count * self.invasion_settings.shooter_reward
        self._increase_invasion_gauge(gained_points)
        return destroyed_shooter_count

    def _resolve_beam_boss_collisions(self) -> int:
        if self.boss is None:
            return 0

        remaining_beams: list[Beam] = []
        hit_count = 0

        for beam in self.beams:
            if rectangles_overlap(beam, self.boss):
                hit_count += 1
            else:
                remaining_beams.append(beam)

        self.beams = remaining_beams
        self.boss.take_damage(hit_count)

        if self.boss.is_defeated:
            self.status = GameStatus.GAME_CLEAR

        return hit_count

    def _increase_invasion_gauge(self, points: int) -> None:
        self.invasion_gauge = min(
            self.invasion_gauge + points,
            self.invasion_settings.target,
        )

    def _resolve_player_damage_collisions(self) -> PlayerHitSource | None:
        meteor_count_before_collision = len(self.meteors)
        chaser_count_before_collision = len(self.chasers)
        shooter_count_before_collision = len(self.shooters)
        projectile_count_before_collision = len(self.enemy_projectiles)

        self.meteors = [
            meteor for meteor in self.meteors if not rectangles_overlap(self.player, meteor)
        ]
        self.chasers = [
            chaser for chaser in self.chasers if not rectangles_overlap(self.player, chaser)
        ]
        self.shooters = [
            shooter for shooter in self.shooters if not rectangles_overlap(self.player, shooter)
        ]
        self.enemy_projectiles = [
            projectile
            for projectile in self.enemy_projectiles
            if not rectangles_overlap(self.player, projectile)
        ]

        contact_touched_player = (
            len(self.meteors) < meteor_count_before_collision
            or len(self.chasers) < chaser_count_before_collision
            or len(self.shooters) < shooter_count_before_collision
        )
        projectile_touched_player = len(self.enemy_projectiles) < projectile_count_before_collision
        player_hit_source = None
        hazard_touched_player = contact_touched_player or projectile_touched_player
        if hazard_touched_player:
            player_was_hit = self.player.take_damage(
                damage=1,
                invincibility_seconds=self.player_settings.invincibility_seconds,
            )
            if player_was_hit:
                player_hit_source = (
                    PlayerHitSource.ENEMY_PROJECTILE
                    if projectile_touched_player
                    else PlayerHitSource.CONTACT
                )

        if self.player.is_defeated:
            self.status = GameStatus.GAME_OVER

        return player_hit_source


def _create_player(
    world_width: int,
    world_height: int,
    playfield_top: int,
    settings: PlayerSettings,
) -> Player:
    return Player(
        x=min(PLAYER_START_X, float(world_width - settings.width)),
        y=(playfield_top + world_height - settings.height) / 2,
        width=settings.width,
        height=settings.height,
        health=settings.max_health,
    )


def _check_positive(value: int | float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name}は0より大きくしてください")
