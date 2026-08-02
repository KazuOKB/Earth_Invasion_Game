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


def _create_session() -> GameSession:
    return GameSession.create(
        world_width=750,
        world_height=500,
        player_width=57,
        player_height=38,
        movement_speed=240.0,
    )
