"""ゲーム全体の進行状態。"""

from enum import Enum


class GameStatus(Enum):
    """プレイ中か、終了しているかを表す。"""

    PLAYING = "playing"
    GAME_OVER = "game_over"
