"""プレイヤー移動と画面端の制限を確認する。"""

from __future__ import annotations

import math
import random

import pytest

from earth_invasion.gameplay.commands import PlayerCommand
from earth_invasion.gameplay.entities import Beam, Chaser, EnemyProjectile, Meteor, Shooter
from earth_invasion.gameplay.events import PlayerHitSource
from earth_invasion.gameplay.session import GameSession
from earth_invasion.gameplay.settings import (
    BossSettings,
    ChaserSettings,
    InvasionSettings,
    MeteorSettings,
    PlayerSettings,
    ScoreSettings,
    ShooterSettings,
    WeaponSettings,
)
from earth_invasion.gameplay.stage import GamePhase, StageSchedule


def test_player_starts_on_left_and_vertical_center() -> None:
    session = _create_session()

    assert session.player.x == 100.0
    assert session.player.y == 231.0
    assert session.player.health == 3


def test_player_starts_below_hud_and_stops_at_playfield_top() -> None:
    session = _create_session(playfield_top=100)

    assert session.player.y == 281.0

    session.update(PlayerCommand(vertical_direction=-1), elapsed_seconds=10.0)

    assert session.player.y == 100.0


def test_invalid_playfield_top_is_rejected() -> None:
    with pytest.raises(ValueError, match="playfield_top"):
        _create_session(playfield_top=500)


def test_player_moves_at_configured_speed() -> None:
    session = _create_session()

    session.update(PlayerCommand(vertical_direction=1), elapsed_seconds=0.5)

    assert session.player.y == 351.0


def test_player_stops_at_top_edge() -> None:
    session = _create_session()

    session.update(PlayerCommand(vertical_direction=-1), elapsed_seconds=10.0)

    assert session.player.y == 0.0


def test_player_stops_at_bottom_edge() -> None:
    session = _create_session()

    session.update(PlayerCommand(vertical_direction=1), elapsed_seconds=10.0)

    assert session.player.y == 462.0


def test_invalid_vertical_direction_is_rejected() -> None:
    with pytest.raises(ValueError, match="vertical_direction"):
        PlayerCommand(vertical_direction=2)


def test_beam_is_fired_from_player_center() -> None:
    session = _create_session()

    events = session.update(PlayerCommand(fire_pressed=True), elapsed_seconds=0.1)

    assert events.beam_fired
    assert len(session.beams) == 1
    assert session.beams[0].x == 157.0
    assert session.beams[0].y == 247.0


def test_beam_cannot_fire_before_cooldown_finishes() -> None:
    session = _create_session()
    fire_command = PlayerCommand(fire_pressed=True)

    session.update(fire_command, elapsed_seconds=0.1)
    session.update(fire_command, elapsed_seconds=0.24)

    assert len(session.beams) == 1

    session.update(fire_command, elapsed_seconds=0.01)

    assert len(session.beams) == 2


def test_beam_moves_at_configured_speed() -> None:
    session = _create_session()
    session.update(PlayerCommand(fire_pressed=True), elapsed_seconds=0.1)

    session.update(PlayerCommand(), elapsed_seconds=0.5)

    assert session.beams[0].x == 457.0


def test_beam_is_removed_after_leaving_screen() -> None:
    session = _create_session()
    session.update(PlayerCommand(fire_pressed=True), elapsed_seconds=0.1)

    session.update(PlayerCommand(), elapsed_seconds=1.0)

    assert session.beams == []


def test_meteor_spawns_after_configured_interval() -> None:
    session = _create_session()

    session.update(PlayerCommand(), elapsed_seconds=1.19)

    assert session.meteors == []

    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert len(session.meteors) == 1


def test_meteor_spawns_inside_vertical_range_with_configured_speed() -> None:
    session = _create_session()

    session.update(PlayerCommand(), elapsed_seconds=1.2)

    meteor = session.meteors[0]
    assert meteor.x == 750.0
    assert 0.0 <= meteor.y <= 370.0
    assert 180.0 <= meteor.speed <= 300.0


def test_meteor_randomness_is_repeatable_with_same_seed() -> None:
    first_session = _create_session(random_seed=10)
    second_session = _create_session(random_seed=10)

    first_session.update(PlayerCommand(), elapsed_seconds=1.2)
    second_session.update(PlayerCommand(), elapsed_seconds=1.2)

    assert first_session.meteors == second_session.meteors


def test_meteor_moves_at_its_own_speed() -> None:
    session = _create_session()
    session.update(PlayerCommand(), elapsed_seconds=1.2)
    meteor = session.meteors[0]

    session.update(PlayerCommand(), elapsed_seconds=0.5)

    assert meteor.x == pytest.approx(750.0 - meteor.speed * 0.5)


def test_meteor_is_removed_after_leaving_screen() -> None:
    session = _create_session()
    session.update(PlayerCommand(), elapsed_seconds=1.2)
    meteor = session.meteors[0]
    meteor.x = -float(meteor.width)

    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert session.meteors == []


def test_beam_destroys_meteor_and_increases_invasion_gauge() -> None:
    session = _create_session()
    session.beams.append(Beam(x=300.0, y=200.0))
    session.meteors.append(_create_meteor(x=310.0, y=190.0))

    events = session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert events.enemies_destroyed == 1
    assert session.beams == []
    assert session.meteors == []
    assert session.invasion_gauge == 2
    assert session.score == 100


def test_beam_and_meteor_remain_when_they_do_not_overlap() -> None:
    session = _create_session()
    session.beams.append(Beam(x=200.0, y=200.0))
    session.meteors.append(_create_meteor(x=600.0, y=200.0))

    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert len(session.beams) == 1
    assert len(session.meteors) == 1
    assert session.invasion_gauge == 0


def test_one_beam_destroys_only_one_meteor() -> None:
    session = _create_session()
    session.beams.append(Beam(x=300.0, y=200.0))
    session.meteors.extend(
        [
            _create_meteor(x=310.0, y=190.0),
            _create_meteor(x=315.0, y=195.0),
        ]
    )

    events = session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert events.enemies_destroyed == 1
    assert session.beams == []
    assert len(session.meteors) == 1
    assert session.invasion_gauge == 2


def test_invasion_gauge_stops_at_target() -> None:
    session = _create_session()
    session.invasion_gauge = 99
    session.beams.append(Beam(x=300.0, y=200.0))
    session.meteors.append(_create_meteor(x=310.0, y=190.0))

    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert session.invasion_gauge == 100
    assert session.invasion_gauge_is_full


def test_destroying_meteor_can_unlock_boss_phase() -> None:
    session = _create_session()
    session.invasion_gauge = 99
    session.stage.update(elapsed_seconds=135.0, invasion_gauge_is_full=False)
    session.beams.append(Beam(x=300.0, y=200.0))
    session.meteors.append(_create_meteor(x=310.0, y=190.0))

    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert session.invasion_gauge_is_full
    assert session.current_phase is GamePhase.BOSS


def test_chaser_spawns_only_after_entering_chaser_phase() -> None:
    session = _create_session()

    session.update(PlayerCommand(), elapsed_seconds=0.8)

    assert session.chasers == []

    session.stage.update(elapsed_seconds=29.2, invasion_gauge_is_full=False)
    session.update(PlayerCommand(), elapsed_seconds=0.8)

    assert len(session.chasers) == 1


def test_chaser_spawns_inside_vertical_range() -> None:
    session = _create_session()
    session.stage.update(elapsed_seconds=30.0, invasion_gauge_is_full=False)

    session.update(PlayerCommand(), elapsed_seconds=0.8)

    chaser = session.chasers[0]
    assert chaser.x == 750.0
    assert 0.0 <= chaser.y <= 471.0


def test_meteor_and_chaser_stop_spawning_after_chaser_phase() -> None:
    session = _create_session()
    session.stage.update(elapsed_seconds=75.0, invasion_gauge_is_full=False)

    session.update(PlayerCommand(), elapsed_seconds=1.2)

    assert session.current_phase is GamePhase.SHOOTER
    assert session.meteors == []
    assert session.chasers == []


def test_chaser_randomness_is_repeatable_with_same_seed() -> None:
    first_session = _create_session(random_seed=10)
    second_session = _create_session(random_seed=10)
    first_session.stage.update(elapsed_seconds=30.0, invasion_gauge_is_full=False)
    second_session.stage.update(elapsed_seconds=30.0, invasion_gauge_is_full=False)

    first_session.update(PlayerCommand(), elapsed_seconds=0.8)
    second_session.update(PlayerCommand(), elapsed_seconds=0.8)

    assert first_session.chasers == second_session.chasers


def test_chaser_moves_left_and_tracks_player() -> None:
    session = _create_session()
    session.chasers.append(_create_chaser(x=500.0, y=0.0))

    session.update(PlayerCommand(), elapsed_seconds=0.5)

    chaser = session.chasers[0]
    assert chaser.x == 380.0
    assert chaser.y == 90.0


def test_chaser_does_not_move_past_player_center() -> None:
    session = _create_session()
    player_center_y = session.player.y + session.player.height / 2
    session.chasers.append(_create_chaser(x=500.0, y=player_center_y - 20.0))

    session.update(PlayerCommand(), elapsed_seconds=1.0)

    chaser = session.chasers[0]
    assert chaser.y + chaser.height / 2 == player_center_y


def test_chaser_is_removed_after_leaving_screen() -> None:
    session = _create_session()
    chaser = _create_chaser(x=-35.0, y=200.0)
    session.chasers.append(chaser)

    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert session.chasers == []


def test_beam_destroys_chaser_and_increases_invasion_gauge() -> None:
    session = _create_session()
    session.beams.append(Beam(x=300.0, y=200.0))
    session.chasers.append(_create_chaser(x=310.0, y=195.0))

    events = session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert events.enemies_destroyed == 1
    assert session.beams == []
    assert session.chasers == []
    assert session.invasion_gauge == 5
    assert session.score == 300


def test_shooter_spawns_only_after_entering_shooter_phase() -> None:
    session = _create_session()

    session.update(PlayerCommand(), elapsed_seconds=1.0)

    assert session.shooters == []

    session.stage.update(elapsed_seconds=74.0, invasion_gauge_is_full=False)
    session.update(PlayerCommand(), elapsed_seconds=1.0)

    assert session.current_phase is GamePhase.SHOOTER
    assert len(session.shooters) == 1


def test_shooter_spawns_inside_vertical_range() -> None:
    session = _create_session()
    session.stage.update(elapsed_seconds=75.0, invasion_gauge_is_full=False)

    session.update(PlayerCommand(), elapsed_seconds=1.0)

    shooter = session.shooters[0]
    assert shooter.x == 750.0
    assert 0.0 <= shooter.y <= 460.0


def test_enemies_spawn_below_hud() -> None:
    meteor_session = _create_session(playfield_top=100)
    chaser_session = _create_session(playfield_top=100)
    shooter_session = _create_session(playfield_top=100)
    chaser_session.stage.update(elapsed_seconds=30.0, invasion_gauge_is_full=False)
    shooter_session.stage.update(elapsed_seconds=75.0, invasion_gauge_is_full=False)

    meteor_session.update(PlayerCommand(), elapsed_seconds=1.2)
    chaser_session.update(PlayerCommand(), elapsed_seconds=0.8)
    shooter_session.update(PlayerCommand(), elapsed_seconds=1.0)

    assert meteor_session.meteors[0].y >= 100.0
    assert chaser_session.chasers[0].y >= 100.0
    assert shooter_session.shooters[0].y >= 100.0


def test_shooter_randomness_is_repeatable_with_same_seed() -> None:
    first_session = _create_session(random_seed=10)
    second_session = _create_session(random_seed=10)
    first_session.stage.update(elapsed_seconds=75.0, invasion_gauge_is_full=False)
    second_session.stage.update(elapsed_seconds=75.0, invasion_gauge_is_full=False)

    first_session.update(PlayerCommand(), elapsed_seconds=1.0)
    second_session.update(PlayerCommand(), elapsed_seconds=1.0)

    assert first_session.shooters == second_session.shooters


def test_shooter_moves_left_and_is_removed_after_leaving_screen() -> None:
    session = _create_session()
    shooter = _create_shooter(x=500.0, y=200.0)
    session.shooters.append(shooter)

    session.update(PlayerCommand(), elapsed_seconds=0.5)

    assert shooter.x == 440.0

    shooter.x = -float(shooter.width)
    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert session.shooters == []


def test_shooter_fires_toward_player_after_configured_interval() -> None:
    session = _create_session()
    session.stage.update(elapsed_seconds=75.0, invasion_gauge_is_full=False)
    session.shooters.append(_create_shooter(x=600.0, y=100.0))

    session.update(PlayerCommand(), elapsed_seconds=0.79)

    assert session.enemy_projectiles == []

    session.update(PlayerCommand(), elapsed_seconds=0.01)

    projectile = session.enemy_projectiles[0]
    assert projectile.velocity_x < 0.0
    assert math.hypot(projectile.velocity_x, projectile.velocity_y) == pytest.approx(300.0)


def test_enemy_projectile_moves_and_is_removed_outside_screen() -> None:
    session = _create_session()
    projectile = EnemyProjectile(
        x=500.0,
        y=200.0,
        velocity_x=-300.0,
        velocity_y=0.0,
    )
    session.enemy_projectiles.append(projectile)

    session.update(PlayerCommand(), elapsed_seconds=0.5)

    assert projectile.x == 350.0

    projectile.x = -float(projectile.width)
    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert session.enemy_projectiles == []


def test_enemy_projectile_is_removed_after_entering_hud() -> None:
    session = _create_session(playfield_top=100)
    session.enemy_projectiles.append(
        EnemyProjectile(
            x=500.0,
            y=99.0,
            velocity_x=0.0,
            velocity_y=0.0,
        )
    )

    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert session.enemy_projectiles == []


def test_beam_destroys_shooter_and_increases_invasion_gauge() -> None:
    session = _create_session()
    session.beams.append(Beam(x=300.0, y=200.0))
    session.shooters.append(_create_shooter(x=310.0, y=195.0))

    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert session.beams == []
    assert session.shooters == []
    assert session.invasion_gauge == 10
    assert session.score == 500


def test_shooter_contact_damages_player_and_removes_shooter() -> None:
    session = _create_session()
    session.shooters.append(_create_shooter(x=120.0, y=220.0))

    events = session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert events.player_was_hit
    assert events.player_hit_source is PlayerHitSource.CONTACT
    assert session.player.health == 2
    assert session.shooters == []


def test_enemy_projectile_damages_player_and_is_removed() -> None:
    session = _create_session()
    session.enemy_projectiles.append(
        EnemyProjectile(
            x=120.0,
            y=235.0,
            velocity_x=0.0,
            velocity_y=0.0,
        )
    )

    events = session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert events.player_hit_source is PlayerHitSource.ENEMY_PROJECTILE
    assert session.player.health == 2
    assert session.enemy_projectiles == []


def test_boss_does_not_appear_without_full_invasion_gauge() -> None:
    session = _create_session()

    session.stage.update(elapsed_seconds=135.0, invasion_gauge_is_full=False)
    session.update(PlayerCommand(), elapsed_seconds=1.0)

    assert session.current_phase is GamePhase.SHOOTER
    assert session.boss is None


def test_boss_appears_with_configured_health_and_position() -> None:
    session = _create_session()

    _enter_boss_phase(session)

    assert session.current_phase is GamePhase.BOSS
    assert session.boss is not None
    assert session.boss.x == 537.0
    assert session.boss.y == 175.0
    assert session.boss.health == 20


def test_entering_boss_phase_removes_remaining_enemies_and_projectiles() -> None:
    session = _create_session()
    session.meteors.append(_create_meteor(x=600.0, y=100.0))
    session.chasers.append(_create_chaser(x=600.0, y=100.0))
    session.shooters.append(_create_shooter(x=600.0, y=100.0))
    session.enemy_projectiles.append(
        EnemyProjectile(x=500.0, y=200.0, velocity_x=-300.0, velocity_y=0.0)
    )

    _enter_boss_phase(session)

    assert session.meteors == []
    assert session.chasers == []
    assert session.shooters == []
    assert session.enemy_projectiles == []


def test_boss_moves_vertically_and_turns_at_screen_edge() -> None:
    session = _create_session()
    _enter_boss_phase(session)
    assert session.boss is not None

    session.update(PlayerCommand(), elapsed_seconds=0.5)

    assert session.boss.y == 225.0

    session.boss.y = 350.0
    session.boss.vertical_direction = 1
    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert session.boss.y == 350.0
    assert session.boss.vertical_direction == -1


def test_boss_starts_and_turns_below_hud() -> None:
    session = _create_session(playfield_top=100)
    _enter_boss_phase(session)
    assert session.boss is not None

    assert session.boss.y == 225.0

    session.boss.y = 100.0
    session.boss.vertical_direction = -1
    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert session.boss.y == 100.0
    assert session.boss.vertical_direction == 1


def test_boss_fires_toward_player_after_configured_interval() -> None:
    session = _create_session()
    _enter_boss_phase(session)

    session.update(PlayerCommand(), elapsed_seconds=0.59)

    assert session.enemy_projectiles == []

    session.update(PlayerCommand(), elapsed_seconds=0.01)

    projectile = session.enemy_projectiles[0]
    assert projectile.velocity_x < 0.0
    assert math.hypot(projectile.velocity_x, projectile.velocity_y) == pytest.approx(360.0)


def test_beam_damages_boss_and_is_removed() -> None:
    session = _create_session()
    _enter_boss_phase(session)
    session.beams.append(Beam(x=540.0, y=200.0))

    events = session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert events.boss_hit_count == 1
    assert session.beams == []
    assert session.boss is not None
    assert session.boss.health == 19
    assert session.score == 100


def test_each_overlapping_beam_damages_boss() -> None:
    session = _create_session()
    _enter_boss_phase(session)
    session.beams.extend(
        [
            Beam(x=540.0, y=200.0),
            Beam(x=545.0, y=210.0),
        ]
    )

    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert session.beams == []
    assert session.boss is not None
    assert session.boss.health == 18


def test_defeating_boss_changes_status_to_game_clear() -> None:
    session = _create_session()
    _enter_boss_phase(session)
    assert session.boss is not None
    session.boss.health = 1
    session.beams.append(Beam(x=540.0, y=200.0))

    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert session.boss.is_defeated
    assert session.is_game_clear
    assert session.is_finished
    assert session.score == 2100


def test_game_clear_stops_game_updates() -> None:
    session = _create_session()
    _trigger_game_clear(session)
    assert session.boss is not None
    player_y = session.player.y
    boss_y = session.boss.y
    stage_elapsed_seconds = session.stage.elapsed_seconds

    session.update(
        PlayerCommand(vertical_direction=1, fire_pressed=True),
        elapsed_seconds=0.5,
    )

    assert session.player.y == player_y
    assert session.boss.y == boss_y
    assert session.stage.elapsed_seconds == stage_elapsed_seconds
    assert session.beams == []


def test_restart_after_game_clear_resets_boss_and_status() -> None:
    session = _create_session()
    _trigger_game_clear(session)

    session.restart()

    assert not session.is_finished
    assert session.boss is None
    assert session.current_phase is GamePhase.METEOR
    assert session.invasion_gauge == 0
    assert session.score == 0


def test_meteor_contact_damages_player_and_removes_meteor() -> None:
    session = _create_session()
    session.meteors.append(_create_meteor(x=120.0, y=220.0))

    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert session.player.health == 2
    assert session.player.invincibility_remaining == 1.0
    assert session.meteors == []


def test_chaser_contact_damages_player_and_removes_chaser() -> None:
    session = _create_session()
    session.chasers.append(_create_chaser(x=120.0, y=220.0))

    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert session.player.health == 2
    assert session.chasers == []


def test_simultaneous_enemy_contacts_deal_only_one_damage() -> None:
    session = _create_session()
    session.meteors.append(_create_meteor(x=120.0, y=220.0))
    session.chasers.append(_create_chaser(x=120.0, y=220.0))

    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert session.player.health == 2
    assert session.meteors == []
    assert session.chasers == []


def test_invincibility_prevents_additional_damage() -> None:
    session = _create_session()
    session.meteors.append(_create_meteor(x=120.0, y=220.0))
    session.update(PlayerCommand(), elapsed_seconds=0.01)
    session.meteors.append(_create_meteor(x=200.0, y=220.0))

    events = session.update(PlayerCommand(), elapsed_seconds=0.5)

    assert not events.player_was_hit
    assert session.player.health == 2
    assert session.player.invincibility_remaining == 0.5
    assert session.meteors == []


def test_player_can_take_damage_after_invincibility_finishes() -> None:
    session = _create_session()
    session.meteors.append(_create_meteor(x=120.0, y=220.0))
    session.update(PlayerCommand(), elapsed_seconds=0.01)

    session.update(PlayerCommand(), elapsed_seconds=1.0)
    session.meteors.append(_create_meteor(x=120.0, y=220.0))
    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert session.player.health == 1


def test_player_health_does_not_fall_below_zero() -> None:
    session = _create_session()
    session.player.health = 1
    session.meteors.append(_create_meteor(x=120.0, y=220.0))
    session.update(PlayerCommand(), elapsed_seconds=0.01)
    session.player.invincibility_remaining = 0.0
    session.meteors.append(_create_meteor(x=120.0, y=220.0))

    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert session.player.health == 0
    assert session.player_is_defeated


def test_zero_health_changes_status_to_game_over() -> None:
    session = _create_session()

    _trigger_game_over(session)

    assert session.is_game_over


def test_game_over_stops_game_updates() -> None:
    session = _create_session()
    session.beams.append(Beam(x=200.0, y=100.0))
    session.chasers.append(_create_chaser(x=600.0, y=100.0))
    session.shooters.append(_create_shooter(x=650.0, y=150.0))
    session.enemy_projectiles.append(
        EnemyProjectile(x=500.0, y=200.0, velocity_x=-300.0, velocity_y=0.0)
    )
    _trigger_game_over(session)
    player_y = session.player.y
    beam_x = session.beams[0].x
    chaser_x = session.chasers[0].x
    shooter_x = session.shooters[0].x
    projectile_x = session.enemy_projectiles[0].x
    stage_elapsed_seconds = session.stage.elapsed_seconds
    invincibility_remaining = session.player.invincibility_remaining

    session.update(
        PlayerCommand(vertical_direction=1, fire_pressed=True),
        elapsed_seconds=0.5,
    )

    assert session.player.y == player_y
    assert session.stage.elapsed_seconds == stage_elapsed_seconds
    assert session.player.invincibility_remaining == invincibility_remaining
    assert session.beams[0].x == beam_x
    assert session.chasers[0].x == chaser_x
    assert session.shooters[0].x == shooter_x
    assert session.enemy_projectiles[0].x == projectile_x


def test_restart_resets_all_game_state() -> None:
    session = _create_session()
    session.invasion_gauge = 50
    session.stage.update(elapsed_seconds=30.0, invasion_gauge_is_full=False)
    session.beams.append(Beam(x=300.0, y=200.0))
    session.chasers.append(_create_chaser(x=600.0, y=100.0))
    session.shooters.append(_create_shooter(x=650.0, y=150.0))
    session.enemy_projectiles.append(
        EnemyProjectile(x=500.0, y=200.0, velocity_x=-300.0, velocity_y=0.0)
    )
    _trigger_game_over(session)

    session.restart()

    assert not session.is_game_over
    assert session.player.health == 3
    assert session.player.x == 100.0
    assert session.player.y == 231.0
    assert session.player.invincibility_remaining == 0.0
    assert session.current_phase is GamePhase.METEOR
    assert session.stage.elapsed_seconds == 0.0
    assert session.invasion_gauge == 0
    assert session.beams == []
    assert session.meteors == []
    assert session.chasers == []
    assert session.shooters == []
    assert session.enemy_projectiles == []
    assert session.beam_cooldown_remaining == 0.0
    assert session.meteor_spawn_remaining == 1.2
    assert session.chaser_spawn_remaining == 0.8
    assert session.shooter_spawn_remaining == 1.0


def test_restart_allows_game_updates_again() -> None:
    session = _create_session()
    _trigger_game_over(session)
    session.restart()

    session.update(PlayerCommand(vertical_direction=1), elapsed_seconds=0.5)

    assert session.player.y == 351.0


def _create_session(random_seed: int = 1, playfield_top: int = 0) -> GameSession:
    return GameSession.create(
        world_width=750,
        world_height=500,
        playfield_top=playfield_top,
        player_settings=PlayerSettings(
            width=57,
            height=38,
            movement_speed=240.0,
            max_health=3,
            invincibility_seconds=1.0,
        ),
        weapon_settings=WeaponSettings(
            beam_speed=600.0,
            beam_cooldown_seconds=0.25,
        ),
        meteor_settings=MeteorSettings(
            width=130,
            height=130,
            spawn_interval_seconds=1.2,
            minimum_speed=180.0,
            maximum_speed=300.0,
        ),
        chaser_settings=ChaserSettings(
            width=35,
            height=29,
            spawn_interval_seconds=0.8,
            horizontal_speed=240.0,
            tracking_speed=180.0,
        ),
        shooter_settings=ShooterSettings(
            width=60,
            height=40,
            spawn_interval_seconds=1.0,
            horizontal_speed=120.0,
            shot_interval_seconds=0.8,
            projectile_speed=300.0,
        ),
        boss_settings=BossSettings(
            width=173,
            height=150,
            max_health=20,
            vertical_speed=100.0,
            shot_interval_seconds=0.6,
            projectile_speed=360.0,
        ),
        invasion_settings=InvasionSettings(
            target=100,
            meteor_reward=2,
            chaser_reward=5,
            shooter_reward=10,
        ),
        score_settings=ScoreSettings(
            meteor_reward=100,
            chaser_reward=300,
            shooter_reward=500,
            boss_hit_reward=100,
            clear_bonus=2000,
        ),
        stage_schedule=StageSchedule(
            meteor_duration_seconds=30.0,
            chaser_duration_seconds=45.0,
            shooter_duration_seconds=60.0,
        ),
        random_source=random.Random(random_seed),
    )


def _create_meteor(x: float, y: float) -> Meteor:
    return Meteor(
        x=x,
        y=y,
        width=130,
        height=130,
        speed=180.0,
    )


def _create_chaser(x: float, y: float) -> Chaser:
    return Chaser(
        x=x,
        y=y,
        width=35,
        height=29,
        horizontal_speed=240.0,
        tracking_speed=180.0,
    )


def _create_shooter(x: float, y: float, shot_cooldown: float = 0.8) -> Shooter:
    return Shooter(
        x=x,
        y=y,
        width=60,
        height=40,
        horizontal_speed=120.0,
        shot_cooldown_remaining=shot_cooldown,
    )


def _trigger_game_over(session: GameSession) -> None:
    session.player.health = 1
    session.meteors.append(_create_meteor(x=120.0, y=220.0))
    session.update(PlayerCommand(), elapsed_seconds=0.01)


def _enter_boss_phase(session: GameSession) -> None:
    session.invasion_gauge = session.invasion_settings.target
    session.stage.update(elapsed_seconds=134.99, invasion_gauge_is_full=True)
    session.update(PlayerCommand(), elapsed_seconds=0.01)


def _trigger_game_clear(session: GameSession) -> None:
    _enter_boss_phase(session)
    assert session.boss is not None
    session.boss.health = 1
    session.beams.append(Beam(x=540.0, y=200.0))
    session.update(PlayerCommand(), elapsed_seconds=0.01)
