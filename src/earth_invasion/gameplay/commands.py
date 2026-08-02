"""ゲーム状態を更新するための入力。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlayerCommand:
    """1回の更新で使うプレイヤー操作。"""

    vertical_direction: int = 0

    def __post_init__(self) -> None:
        if self.vertical_direction not in (-1, 0, 1):
            raise ValueError("vertical_directionは-1、0、1のいずれかにしてください")
