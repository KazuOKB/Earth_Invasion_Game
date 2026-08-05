"""1回のゲーム更新で起きた出来事。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PlayerHitSource(Enum):
    """プレイヤーがダメージを受けた原因。"""

    CONTACT = "contact"
    ENEMY_PROJECTILE = "enemy_projectile"


@dataclass(frozen=True, slots=True)
class GameplayEvents:
    """描画や音へ伝えるゲーム上の出来事。"""

    beam_fired: bool = False
    enemies_destroyed: int = 0
    boss_hit_count: int = 0
    player_hit_source: PlayerHitSource | None = None

    @property
    def player_was_hit(self) -> bool:
        """今回プレイヤーがダメージを受けたか返す。"""

        return self.player_hit_source is not None
