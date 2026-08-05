"""1回のゲーム更新で起きた出来事。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GameplayEvents:
    """描画や音へ伝えるゲーム上の出来事。"""

    beam_fired: bool = False
    enemies_destroyed: int = 0
    boss_hit_count: int = 0
    player_was_hit: bool = False
