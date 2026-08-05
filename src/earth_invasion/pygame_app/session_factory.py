"""設定と画像からゲームセッションを組み立てる。"""

from __future__ import annotations

import random

from earth_invasion.configuration import ApplicationConfig
from earth_invasion.gameplay.session import GameSession
from earth_invasion.gameplay.settings import (
    BossSettings,
    ChaserSettings,
    InvasionSettings,
    MeteorSettings,
    PlayerSettings,
    ShooterSettings,
    WeaponSettings,
)
from earth_invasion.gameplay.stage import StageSchedule
from earth_invasion.pygame_app.assets import GameImages
from earth_invasion.pygame_app.hud import HUD_HEIGHT


def create_game_session(
    config: ApplicationConfig,
    images: GameImages,
    random_source: random.Random | None = None,
) -> GameSession:
    """読み込んだ設定と画像サイズをゲームルール用の値へ変換する。"""

    gameplay = config.gameplay
    stage = config.stage
    player_width, player_height = images.player.get_size()
    meteor_width, meteor_height = images.meteor.get_size()
    chaser_width, chaser_height = images.chaser.get_size()
    shooter_width, shooter_height = images.shooter.get_size()
    boss_width, boss_height = images.boss.get_size()
    session_random = random_source if random_source is not None else random.Random()

    return GameSession.create(
        world_width=gameplay.logical_resolution.width,
        world_height=gameplay.logical_resolution.height,
        playfield_top=HUD_HEIGHT,
        player_settings=PlayerSettings(
            width=player_width,
            height=player_height,
            movement_speed=gameplay.player.movement_speed_pixels_per_second,
            max_health=gameplay.player.max_health,
            invincibility_seconds=gameplay.player.invincibility_seconds,
        ),
        weapon_settings=WeaponSettings(
            beam_speed=gameplay.weapon.beam_speed_pixels_per_second,
            beam_cooldown_seconds=gameplay.weapon.beam_cooldown_seconds,
        ),
        meteor_settings=MeteorSettings(
            width=meteor_width,
            height=meteor_height,
            spawn_interval_seconds=gameplay.meteor.spawn_interval_seconds,
            minimum_speed=gameplay.meteor.minimum_speed_pixels_per_second,
            maximum_speed=gameplay.meteor.maximum_speed_pixels_per_second,
        ),
        chaser_settings=ChaserSettings(
            width=chaser_width,
            height=chaser_height,
            spawn_interval_seconds=gameplay.chaser.spawn_interval_seconds,
            horizontal_speed=gameplay.chaser.horizontal_speed_pixels_per_second,
            tracking_speed=gameplay.chaser.tracking_speed_pixels_per_second,
        ),
        shooter_settings=ShooterSettings(
            width=shooter_width,
            height=shooter_height,
            spawn_interval_seconds=gameplay.shooter.spawn_interval_seconds,
            horizontal_speed=gameplay.shooter.horizontal_speed_pixels_per_second,
            shot_interval_seconds=gameplay.shooter.shot_interval_seconds,
            projectile_speed=gameplay.shooter.projectile_speed_pixels_per_second,
        ),
        boss_settings=BossSettings(
            width=boss_width,
            height=boss_height,
            max_health=gameplay.boss.max_health,
            vertical_speed=gameplay.boss.vertical_speed_pixels_per_second,
            shot_interval_seconds=gameplay.boss.shot_interval_seconds,
            projectile_speed=gameplay.boss.projectile_speed_pixels_per_second,
        ),
        invasion_settings=InvasionSettings(
            target=stage.invasion_target,
            meteor_reward=gameplay.invasion_rewards.meteor,
            chaser_reward=gameplay.invasion_rewards.chaser,
            shooter_reward=gameplay.invasion_rewards.shooter,
        ),
        stage_schedule=StageSchedule(
            meteor_duration_seconds=stage.duration_seconds_for("meteor"),
            chaser_duration_seconds=stage.duration_seconds_for("chaser"),
            shooter_duration_seconds=stage.duration_seconds_for("shooter"),
        ),
        random_source=session_random,
    )
