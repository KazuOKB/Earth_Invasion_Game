"""ゲームを一定間隔で更新するための時間管理。"""

from __future__ import annotations

from dataclasses import dataclass, field

MAX_FRAME_SECONDS = 0.25


@dataclass(slots=True)
class FixedTimeStep:
    """経過時間を固定更新の回数へ変換する。"""

    updates_per_second: int
    max_frame_seconds: float = MAX_FRAME_SECONDS
    accumulated_seconds: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        if self.updates_per_second <= 0:
            raise ValueError("updates_per_secondは0より大きくしてください")
        if self.max_frame_seconds <= 0:
            raise ValueError("max_frame_secondsは0より大きくしてください")

    @property
    def step_seconds(self) -> float:
        """ゲームを1回更新するときの秒数。"""

        return 1.0 / self.updates_per_second

    def consume(self, elapsed_seconds: float) -> int:
        """今回必要な固定更新の回数を返す。"""

        if elapsed_seconds < 0:
            raise ValueError("elapsed_secondsは0以上にしてください")

        self.accumulated_seconds += min(elapsed_seconds, self.max_frame_seconds)
        update_count = 0

        while self.accumulated_seconds >= self.step_seconds:
            self.accumulated_seconds -= self.step_seconds
            update_count += 1

        return update_count

    def reset(self) -> None:
        """画面切り替え前に残っていた時間を破棄する。"""

        self.accumulated_seconds = 0.0
