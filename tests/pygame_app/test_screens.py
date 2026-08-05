"""タイトルと結果画面をランキング付きで描画できることを確認する。"""

from __future__ import annotations

import pygame

from earth_invasion.pygame_app.navigation import AppScreen
from earth_invasion.pygame_app.screens import draw_result_screen, draw_title_screen
from earth_invasion.pygame_app.volume import VolumeControl


def test_title_and_result_screens_draw_ranking() -> None:
    font_was_initialized = pygame.font.get_init()
    pygame.font.init()
    try:
        surface = pygame.Surface((750, 500))
        background = pygame.Surface((750, 500))
        title_font = pygame.font.Font(None, 72)
        result_font = pygame.font.Font(None, 48)
        text_font = pygame.font.Font(None, 30)
        ranking = (5000, 4000, 3000, 2000, 1000)

        draw_title_screen(
            surface,
            background,
            title_font,
            text_font,
            VolumeControl(0.0, 0.0),
            ranking,
        )
        draw_result_screen(
            surface,
            background,
            result_font,
            text_font,
            AppScreen.GAME_CLEAR,
            5000,
            ranking,
        )
    finally:
        if not font_was_initialized:
            pygame.font.quit()
