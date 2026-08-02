"""Pygameの入力をゲーム用の命令へ変換する。"""

from __future__ import annotations

from earth_invasion.gameplay.commands import PlayerCommand


def create_player_command(*, up_pressed: bool, down_pressed: bool) -> PlayerCommand:
    """上下キーの状態からプレイヤー操作を作る。"""

    vertical_direction = int(down_pressed) - int(up_pressed)
    return PlayerCommand(vertical_direction=vertical_direction)
