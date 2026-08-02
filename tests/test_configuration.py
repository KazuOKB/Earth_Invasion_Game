"""ゲーム設定の読み込みテスト。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from earth_invasion.configuration import (
    ConfigError,
    load_application_config,
    load_gameplay_config,
    load_stage_config,
)


def test_normal_profile_loads_expected_values() -> None:
    config = load_application_config("normal")

    assert config.gameplay.logical_resolution.width == 750
    assert config.gameplay.logical_resolution.height == 500
    assert config.gameplay.player.max_health == 3
    assert config.gameplay.player.invincibility_seconds == 1.0
    assert config.gameplay.player.movement_speed_pixels_per_second == 240.0
    assert config.gameplay.weapon.beam_cooldown_seconds == 0.25
    assert config.gameplay.weapon.beam_speed_pixels_per_second == 600.0
    assert config.gameplay.meteor.spawn_interval_seconds == 1.2
    assert config.gameplay.meteor.minimum_speed_pixels_per_second == 180.0
    assert config.gameplay.meteor.maximum_speed_pixels_per_second == 300.0
    assert config.gameplay.invasion_rewards.meteor == 2
    assert config.gameplay.invasion_rewards.chaser == 5
    assert config.gameplay.invasion_rewards.shooter == 10
    assert config.stage.profile == "normal"
    assert config.stage.invasion_target == 100
    assert [phase.id for phase in config.stage.phases] == [
        "meteor",
        "chaser",
        "shooter",
        "boss",
    ]


def test_test_profile_uses_short_durations() -> None:
    config = load_application_config("test")

    assert config.stage.invasion_target == 10
    assert [phase.duration_seconds for phase in config.stage.phases] == [
        2.0,
        2.0,
        2.0,
        None,
    ]


def test_unknown_profile_is_rejected() -> None:
    with pytest.raises(ConfigError, match="不明なステージ設定"):
        load_application_config("unknown")


def test_non_positive_health_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "gameplay.json"
    data = _gameplay_config_data()
    player = data["player"]
    assert isinstance(player, dict)
    player["max_health"] = 0
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ConfigError, match="max_health"):
        load_gameplay_config(path)


def test_non_positive_movement_speed_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "gameplay.json"
    data = _gameplay_config_data()
    player = data["player"]
    assert isinstance(player, dict)
    player["movement_speed_pixels_per_second"] = 0
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ConfigError, match="movement_speed_pixels_per_second"):
        load_gameplay_config(path)


def test_non_positive_beam_speed_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "gameplay.json"
    data = _gameplay_config_data()
    weapon = data["weapon"]
    assert isinstance(weapon, dict)
    weapon["beam_speed_pixels_per_second"] = 0
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ConfigError, match="beam_speed_pixels_per_second"):
        load_gameplay_config(path)


def test_meteor_minimum_speed_cannot_exceed_maximum(tmp_path: Path) -> None:
    path = tmp_path / "gameplay.json"
    data = _gameplay_config_data()
    meteor = data["meteor"]
    assert isinstance(meteor, dict)
    meteor["minimum_speed_pixels_per_second"] = 301.0
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ConfigError, match="最低速度"):
        load_gameplay_config(path)


def test_non_positive_duration_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "stage.json"
    _write_stage_config(path, meteor_duration=0)

    with pytest.raises(ConfigError, match="duration_seconds"):
        load_stage_config(path)


def test_wrong_phase_order_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "stage.json"
    data = _stage_config_data(meteor_duration=10)
    phases = data["phases"]
    assert isinstance(phases, list)
    phases[0], phases[1] = phases[1], phases[0]
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ConfigError, match="区間の順番"):
        load_stage_config(path)


def test_boss_duration_must_be_null(tmp_path: Path) -> None:
    path = tmp_path / "stage.json"
    data = _stage_config_data(meteor_duration=10)
    phases = data["phases"]
    assert isinstance(phases, list)
    boss = phases[-1]
    assert isinstance(boss, dict)
    boss["duration_seconds"] = 10
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ConfigError, match="boss"):
        load_stage_config(path)


def test_boss_duration_is_required(tmp_path: Path) -> None:
    path = tmp_path / "stage.json"
    data = _stage_config_data(meteor_duration=10)
    phases = data["phases"]
    assert isinstance(phases, list)
    boss = phases[-1]
    assert isinstance(boss, dict)
    del boss["duration_seconds"]
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ConfigError, match="duration_seconds"):
        load_stage_config(path)


def _write_stage_config(path: Path, meteor_duration: int) -> None:
    path.write_text(
        json.dumps(_stage_config_data(meteor_duration)),
        encoding="utf-8",
    )


def _stage_config_data(meteor_duration: int) -> dict[str, object]:
    return {
        "profile": "normal",
        "invasion_target": 100,
        "phases": [
            {"id": "meteor", "duration_seconds": meteor_duration},
            {"id": "chaser", "duration_seconds": 20},
            {"id": "shooter", "duration_seconds": 30},
            {"id": "boss", "duration_seconds": None},
        ],
    }


def _gameplay_config_data() -> dict[str, object]:
    return {
        "logical_resolution": {"width": 750, "height": 500},
        "updates_per_second": 60,
        "player": {
            "max_health": 3,
            "invincibility_seconds": 1.0,
            "movement_speed_pixels_per_second": 240.0,
        },
        "weapon": {
            "beam_cooldown_seconds": 0.25,
            "beam_speed_pixels_per_second": 600.0,
        },
        "meteor": {
            "spawn_interval_seconds": 1.2,
            "minimum_speed_pixels_per_second": 180.0,
            "maximum_speed_pixels_per_second": 300.0,
        },
        "invasion_rewards": {"meteor": 2, "chaser": 5, "shooter": 10},
    }
