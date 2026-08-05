"""ゲーム画面に表示する短い演出。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DamageFlash:
    """被弾直後だけ画面を赤くする時間を管理する。"""

    duration_seconds: float = 0.18
    remaining_seconds: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        if self.duration_seconds <= 0:
            raise ValueError("duration_secondsは0より大きくしてください")

    @property
    def intensity(self) -> float:
        """現在の強さを0から1の範囲で返す。"""

        return self.remaining_seconds / self.duration_seconds

    @property
    def is_visible(self) -> bool:
        """フラッシュを表示する必要があるか返す。"""

        return self.remaining_seconds > 0.0

    def trigger(self) -> None:
        """被弾フラッシュを最初から表示する。"""

        self.remaining_seconds = self.duration_seconds

    def update(self, elapsed_seconds: float) -> None:
        """経過時間に応じてフラッシュを弱くする。"""

        if elapsed_seconds < 0:
            raise ValueError("elapsed_secondsは0以上にしてください")

        self.remaining_seconds = max(self.remaining_seconds - elapsed_seconds, 0.0)

    def reset(self) -> None:
        """フラッシュを消す。"""

        self.remaining_seconds = 0.0
