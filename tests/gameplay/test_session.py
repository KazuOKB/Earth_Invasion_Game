"""プレイヤー移動と画面端の制限を確認する。"""

from __future__ import annotations

import pytest

from earth_invasion.gameplay.commands import PlayerCommand
from earth_invasion.gameplay.session import GameSession


def test_player_starts_on_left_and_vertical_center() -> None:
    session = _create_session()

    assert session.player.x == 100.0
    assert session.player.y == 231.0


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


def _create_session() -> GameSession:
    return GameSession.create(
        world_width=750,
        world_height=500,
        player_width=57,
        player_height=38,
        movement_speed=240.0,
        beam_speed=600.0,
        beam_cooldown_seconds=0.25,
    )
