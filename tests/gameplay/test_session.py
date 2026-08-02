"""プレイヤー移動と画面端の制限を確認する。"""

from __future__ import annotations

import random

import pytest

from earth_invasion.gameplay.commands import PlayerCommand
from earth_invasion.gameplay.entities import Beam, Chaser, Meteor
from earth_invasion.gameplay.session import GameSession
from earth_invasion.gameplay.settings import (
    ChaserSettings,
    InvasionSettings,
    MeteorSettings,
    PlayerSettings,
    WeaponSettings,
)
from earth_invasion.gameplay.stage import GamePhase, StageSchedule


def test_player_starts_on_left_and_vertical_center() -> None:
    session = _create_session()

    assert session.player.x == 100.0
    assert session.player.y == 231.0
    assert session.player.health == 3


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

    session.update(PlayerCommand(fire_pressed=True), elapsed_seconds=0.1)

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

    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert session.beams == []
    assert session.meteors == []
    assert session.invasion_gauge == 2


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

    session.update(PlayerCommand(), elapsed_seconds=0.01)

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

    session.update(PlayerCommand(), elapsed_seconds=0.01)

    assert session.beams == []
    assert session.chasers == []
    assert session.invasion_gauge == 5


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

    session.update(PlayerCommand(), elapsed_seconds=0.5)

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


def _create_session(random_seed: int = 1) -> GameSession:
    return GameSession.create(
        world_width=750,
        world_height=500,
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
        invasion_settings=InvasionSettings(
            target=100,
            meteor_reward=2,
            chaser_reward=5,
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
