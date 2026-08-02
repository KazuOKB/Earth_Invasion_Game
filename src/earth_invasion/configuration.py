"""JSON設定を読み込み、ゲームで使う値へ変換する。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import cast

PHASE_ORDER = ("meteor", "chaser", "shooter", "boss")
STAGE_PROFILES = ("normal", "test")
DEFAULT_DATA_PACKAGE = "earth_invasion.data"

JsonObject = dict[str, object]
ConfigFile = Path | Traversable


class ConfigError(ValueError):
    """設定ファイルの内容が正しくない場合に発生する。"""


@dataclass(frozen=True, slots=True)
class LogicalResolution:
    """ゲーム内部で使う固定の画面サイズ。"""

    width: int
    height: int


@dataclass(frozen=True, slots=True)
class PlayerConfig:
    """プレイヤーの基本設定。"""

    max_health: int
    invincibility_seconds: float
    movement_speed_pixels_per_second: float


@dataclass(frozen=True, slots=True)
class WeaponConfig:
    """プレイヤーの武器設定。"""

    beam_cooldown_seconds: float


@dataclass(frozen=True, slots=True)
class InvasionRewards:
    """敵を倒したときに増える侵略ゲージの量。"""

    meteor: int
    chaser: int
    shooter: int


@dataclass(frozen=True, slots=True)
class GameplayConfig:
    """通常用とテスト用で共通するゲーム設定。"""

    logical_resolution: LogicalResolution
    updates_per_second: int
    player: PlayerConfig
    weapon: WeaponConfig
    invasion_rewards: InvasionRewards


@dataclass(frozen=True, slots=True)
class PhaseConfig:
    """1つのステージ区間の設定。"""

    id: str
    duration_seconds: float | None


@dataclass(frozen=True, slots=True)
class StageConfig:
    """選択したプロファイルのステージ設定。"""

    profile: str
    invasion_target: int
    phases: tuple[PhaseConfig, ...]


@dataclass(frozen=True, slots=True)
class ApplicationConfig:
    """起動時に必要な設定をまとめる。"""

    gameplay: GameplayConfig
    stage: StageConfig


def load_application_config(
    profile: str = "normal",
    data_directory: Path | None = None,
) -> ApplicationConfig:
    """共通設定と指定されたステージ設定を読み込む。"""

    if profile not in STAGE_PROFILES:
        choices = ", ".join(STAGE_PROFILES)
        raise ConfigError(f"不明なステージ設定です: {profile}。使用可能: {choices}")

    gameplay = load_gameplay_config(_data_file(data_directory, "gameplay.json"))
    stage = load_stage_config(_data_file(data_directory, f"stages.{profile}.json"))

    if stage.profile != profile:
        raise ConfigError(f"ファイル名の設定は{profile}ですが、profileは{stage.profile}です")

    return ApplicationConfig(gameplay=gameplay, stage=stage)


def load_gameplay_config(path: ConfigFile) -> GameplayConfig:
    """共通ゲーム設定を読み込む。"""

    data = _read_json_object(path)
    resolution = _required_object(data, "logical_resolution", "gameplay")
    player = _required_object(data, "player", "gameplay")
    weapon = _required_object(data, "weapon", "gameplay")
    rewards = _required_object(data, "invasion_rewards", "gameplay")

    return GameplayConfig(
        logical_resolution=LogicalResolution(
            width=_positive_int(resolution, "width", "logical_resolution"),
            height=_positive_int(resolution, "height", "logical_resolution"),
        ),
        updates_per_second=_positive_int(data, "updates_per_second", "gameplay"),
        player=PlayerConfig(
            max_health=_positive_int(player, "max_health", "player"),
            invincibility_seconds=_positive_number(
                player,
                "invincibility_seconds",
                "player",
            ),
            movement_speed_pixels_per_second=_positive_number(
                player,
                "movement_speed_pixels_per_second",
                "player",
            ),
        ),
        weapon=WeaponConfig(
            beam_cooldown_seconds=_positive_number(
                weapon,
                "beam_cooldown_seconds",
                "weapon",
            ),
        ),
        invasion_rewards=InvasionRewards(
            meteor=_positive_int(rewards, "meteor", "invasion_rewards"),
            chaser=_positive_int(rewards, "chaser", "invasion_rewards"),
            shooter=_positive_int(rewards, "shooter", "invasion_rewards"),
        ),
    )


def load_stage_config(path: ConfigFile) -> StageConfig:
    """1つのステージ設定を読み込む。"""

    data = _read_json_object(path)
    profile = _required_string(data, "profile", "stage")
    invasion_target = _positive_int(data, "invasion_target", "stage")
    raw_phases = _required_list(data, "phases", "stage")

    phases = tuple(_parse_phase(value, index) for index, value in enumerate(raw_phases))
    phase_ids = tuple(phase.id for phase in phases)

    if phase_ids != PHASE_ORDER:
        expected = ", ".join(PHASE_ORDER)
        actual = ", ".join(phase_ids)
        raise ConfigError(f"区間の順番が正しくありません。期待値: {expected}、実際: {actual}")

    return StageConfig(
        profile=profile,
        invasion_target=invasion_target,
        phases=phases,
    )


def _parse_phase(value: object, index: int) -> PhaseConfig:
    location = f"phases[{index}]"
    phase = _as_json_object(value, location)
    phase_id = _required_string(phase, "id", location)
    duration = _required_value(phase, "duration_seconds", location)

    if phase_id == "boss":
        if duration is not None:
            raise ConfigError("bossのduration_secondsはnullにしてください")
        return PhaseConfig(id=phase_id, duration_seconds=None)

    if duration is None:
        raise ConfigError(f"{location}.duration_secondsがありません")

    return PhaseConfig(
        id=phase_id,
        duration_seconds=_positive_number_value(duration, f"{location}.duration_seconds"),
    )


def _data_file(data_directory: Path | None, filename: str) -> ConfigFile:
    if data_directory is not None:
        return data_directory / filename
    return files(DEFAULT_DATA_PACKAGE).joinpath(filename)


def _read_json_object(path: ConfigFile) -> JsonObject:
    try:
        text = path.read_text(encoding="utf-8")
        value: object = json.loads(text)
    except FileNotFoundError as error:
        raise ConfigError(f"設定ファイルが見つかりません: {path}") from error
    except json.JSONDecodeError as error:
        raise ConfigError(f"JSONの形式が正しくありません: {path}:{error.lineno}") from error
    except OSError as error:
        raise ConfigError(f"設定ファイルを読み込めません: {path}") from error

    return _as_json_object(value, str(path))


def _as_json_object(value: object, location: str) -> JsonObject:
    if not isinstance(value, dict):
        raise ConfigError(f"{location}はJSONオブジェクトにしてください")

    if not all(isinstance(key, str) for key in value):
        raise ConfigError(f"{location}のキーは文字列にしてください")

    return cast(JsonObject, value)


def _required_object(data: JsonObject, key: str, location: str) -> JsonObject:
    value = _required_value(data, key, location)
    return _as_json_object(value, f"{location}.{key}")


def _required_list(data: JsonObject, key: str, location: str) -> list[object]:
    value = _required_value(data, key, location)
    if not isinstance(value, list):
        raise ConfigError(f"{location}.{key}は配列にしてください")
    return cast(list[object], value)


def _required_string(data: JsonObject, key: str, location: str) -> str:
    value = _required_value(data, key, location)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{location}.{key}は空でない文字列にしてください")
    return value


def _positive_int(data: JsonObject, key: str, location: str) -> int:
    value = _required_value(data, key, location)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConfigError(f"{location}.{key}は0より大きい整数にしてください")
    return value


def _positive_number(data: JsonObject, key: str, location: str) -> float:
    value = _required_value(data, key, location)
    return _positive_number_value(value, f"{location}.{key}")


def _positive_number_value(value: object, location: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or value <= 0:
        raise ConfigError(f"{location}は0より大きい数値にしてください")
    return float(value)


def _required_value(data: JsonObject, key: str, location: str) -> object:
    if key not in data:
        raise ConfigError(f"{location}.{key}がありません")
    return data[key]
