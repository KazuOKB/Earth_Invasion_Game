"""HUDの配置と表示状態。"""

from __future__ import annotations

HUD_HEIGHT = 100


def heart_states(health: int, max_health: int) -> tuple[bool, ...]:
    """最大体力分のハートが満たされているか返す。"""

    if max_health <= 0:
        raise ValueError("max_healthは0より大きくしてください")

    visible_health = min(max(health, 0), max_health)
    return tuple(index < visible_health for index in range(max_health))
