"""画面遷移とキー操作を確認する。"""

from __future__ import annotations

import pytest

from earth_invasion.gameplay.status import GameStatus
from earth_invasion.pygame_app.navigation import (
    AppScreen,
    NavigationAction,
    NavigationKey,
    ScreenFlow,
    action_for_key,
)


@pytest.mark.parametrize(
    ("screen", "key", "expected"),
    [
        (AppScreen.TITLE, NavigationKey.ENTER, NavigationAction.START_GAME),
        (AppScreen.TITLE, NavigationKey.R, NavigationAction.SHOW_RULES),
        (AppScreen.TITLE, NavigationKey.ESCAPE, NavigationAction.CLOSE),
        (AppScreen.RULES, NavigationKey.ENTER, NavigationAction.SHOW_TITLE),
        (AppScreen.RULES, NavigationKey.ESCAPE, NavigationAction.SHOW_TITLE),
        (AppScreen.GAMEPLAY, NavigationKey.ESCAPE, NavigationAction.SHOW_TITLE),
        (AppScreen.GAME_OVER, NavigationKey.R, NavigationAction.RETRY),
        (AppScreen.GAME_CLEAR, NavigationKey.R, NavigationAction.RETRY),
        (AppScreen.GAME_OVER, NavigationKey.ENTER, NavigationAction.SHOW_TITLE),
        (AppScreen.GAME_CLEAR, NavigationKey.ESCAPE, NavigationAction.SHOW_TITLE),
        (AppScreen.GAMEPLAY, NavigationKey.R, NavigationAction.NONE),
    ],
)
def test_key_action_is_selected_for_each_screen(
    screen: AppScreen,
    key: NavigationKey,
    expected: NavigationAction,
) -> None:
    assert action_for_key(screen, key) is expected


def test_screen_flow_starts_at_title() -> None:
    screen_flow = ScreenFlow()

    _assert_current_screen(screen_flow, AppScreen.TITLE)


def test_start_and_return_to_title() -> None:
    screen_flow = ScreenFlow()

    screen_flow.apply(NavigationAction.START_GAME)
    _assert_current_screen(screen_flow, AppScreen.GAMEPLAY)

    screen_flow.apply(NavigationAction.SHOW_TITLE)
    _assert_current_screen(screen_flow, AppScreen.TITLE)


def test_rules_are_opened_from_title() -> None:
    screen_flow = ScreenFlow()

    screen_flow.apply(NavigationAction.SHOW_RULES)

    _assert_current_screen(screen_flow, AppScreen.RULES)


def test_gameplay_result_is_recorded() -> None:
    screen_flow = ScreenFlow(AppScreen.GAMEPLAY)

    screen_flow.show_gameplay_result(GameStatus.GAME_OVER)
    _assert_current_screen(screen_flow, AppScreen.GAME_OVER)

    screen_flow.show_gameplay_result(GameStatus.GAME_CLEAR)
    _assert_current_screen(screen_flow, AppScreen.GAME_CLEAR)


def test_playing_status_keeps_gameplay_screen() -> None:
    screen_flow = ScreenFlow(AppScreen.GAMEPLAY)

    screen_flow.show_gameplay_result(GameStatus.PLAYING)

    _assert_current_screen(screen_flow, AppScreen.GAMEPLAY)


def test_retry_returns_to_gameplay() -> None:
    screen_flow = ScreenFlow(AppScreen.GAME_OVER)

    screen_flow.apply(NavigationAction.RETRY)

    _assert_current_screen(screen_flow, AppScreen.GAMEPLAY)


def _assert_current_screen(screen_flow: ScreenFlow, expected: AppScreen) -> None:
    assert screen_flow.current is expected
