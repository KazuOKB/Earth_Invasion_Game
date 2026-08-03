"""アプリケーションの画面状態とキー操作。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AppScreen(Enum):
    """現在表示している画面。"""

    TITLE = "title"
    RULES = "rules"
    GAMEPLAY = "gameplay"
    GAME_OVER = "game_over"
    GAME_CLEAR = "game_clear"


class NavigationKey(Enum):
    """画面移動に使うキー。"""

    ENTER = "enter"
    R = "r"
    ESCAPE = "escape"
    OTHER = "other"


class NavigationAction(Enum):
    """キーを押した結果として行う操作。"""

    NONE = "none"
    START_GAME = "start_game"
    RETRY = "retry"
    SHOW_RULES = "show_rules"
    SHOW_TITLE = "show_title"
    CLOSE = "close"


@dataclass(slots=True)
class ScreenFlow:
    """画面状態を保持する。"""

    current: AppScreen = AppScreen.TITLE

    def apply(self, action: NavigationAction) -> None:
        """画面移動を伴う操作を反映する。"""

        match action:
            case NavigationAction.START_GAME | NavigationAction.RETRY:
                self.current = AppScreen.GAMEPLAY
            case NavigationAction.SHOW_RULES:
                self.current = AppScreen.RULES
            case NavigationAction.SHOW_TITLE:
                self.current = AppScreen.TITLE
            case NavigationAction.NONE | NavigationAction.CLOSE:
                return

    def show_game_over(self) -> None:
        """ゲームオーバー画面へ移動する。"""

        self.current = AppScreen.GAME_OVER

    def show_game_clear(self) -> None:
        """ゲームクリア画面へ移動する。"""

        self.current = AppScreen.GAME_CLEAR


def action_for_key(screen: AppScreen, key: NavigationKey) -> NavigationAction:
    """現在の画面とキーから操作を決める。"""

    match screen:
        case AppScreen.TITLE:
            if key is NavigationKey.ENTER:
                return NavigationAction.START_GAME
            if key is NavigationKey.R:
                return NavigationAction.SHOW_RULES
            if key is NavigationKey.ESCAPE:
                return NavigationAction.CLOSE
        case AppScreen.RULES:
            if key in (NavigationKey.ENTER, NavigationKey.ESCAPE):
                return NavigationAction.SHOW_TITLE
        case AppScreen.GAMEPLAY:
            if key is NavigationKey.ESCAPE:
                return NavigationAction.SHOW_TITLE
        case AppScreen.GAME_OVER | AppScreen.GAME_CLEAR:
            if key is NavigationKey.R:
                return NavigationAction.RETRY
            if key in (NavigationKey.ENTER, NavigationKey.ESCAPE):
                return NavigationAction.SHOW_TITLE

    return NavigationAction.NONE
