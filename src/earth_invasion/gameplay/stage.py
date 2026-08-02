"""ステージ区間と時間による進行。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

TIME_EPSILON = 1e-9


class GamePhase(Enum):
    """ゲーム中の区間。"""

    METEOR = "meteor"
    CHASER = "chaser"
    SHOOTER = "shooter"
    BOSS = "boss"


@dataclass(frozen=True, slots=True)
class StageSchedule:
    """時間で終了する3区間の長さ。"""

    meteor_duration_seconds: float
    chaser_duration_seconds: float
    shooter_duration_seconds: float

    def __post_init__(self) -> None:
        _check_positive(self.meteor_duration_seconds, "meteor_duration_seconds")
        _check_positive(self.chaser_duration_seconds, "chaser_duration_seconds")
        _check_positive(self.shooter_duration_seconds, "shooter_duration_seconds")

    def duration_for(self, phase: GamePhase) -> float | None:
        """区間の長さを返す。時間制限のないボスはNoneを返す。"""

        match phase:
            case GamePhase.METEOR:
                return self.meteor_duration_seconds
            case GamePhase.CHASER:
                return self.chaser_duration_seconds
            case GamePhase.SHOOTER:
                return self.shooter_duration_seconds
            case GamePhase.BOSS:
                return None


@dataclass(slots=True)
class StageProgress:
    """現在の区間と、その区間で経過した時間。"""

    schedule: StageSchedule
    phase: GamePhase = GamePhase.METEOR
    elapsed_seconds: float = 0.0

    @property
    def remaining_seconds(self) -> float | None:
        """現在区間の残り時間を返す。ボスはNoneを返す。"""

        duration = self.schedule.duration_for(self.phase)
        if duration is None:
            return None
        return max(duration - self.elapsed_seconds, 0.0)

    def update(self, elapsed_seconds: float, invasion_gauge_is_full: bool) -> None:
        """時間を進め、条件を満たした区間を切り替える。"""

        _check_positive(elapsed_seconds, "elapsed_seconds")

        if self.phase is GamePhase.BOSS:
            return

        self.elapsed_seconds += elapsed_seconds

        while self.phase is not GamePhase.BOSS:
            duration = self.schedule.duration_for(self.phase)
            if duration is None:
                return

            if self.elapsed_seconds + TIME_EPSILON < duration:
                return

            if self.phase is GamePhase.SHOOTER and not invasion_gauge_is_full:
                self.elapsed_seconds = duration
                return

            self.elapsed_seconds -= duration
            self.phase = _next_phase(self.phase)

        self.elapsed_seconds = 0.0


def _next_phase(phase: GamePhase) -> GamePhase:
    match phase:
        case GamePhase.METEOR:
            return GamePhase.CHASER
        case GamePhase.CHASER:
            return GamePhase.SHOOTER
        case GamePhase.SHOOTER:
            return GamePhase.BOSS
        case GamePhase.BOSS:
            raise ValueError("ボス区間の次はありません")


def _check_positive(value: float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name}は0より大きくしてください")
