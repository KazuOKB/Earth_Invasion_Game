"""タイトル、ルール、結果画面の描画。"""

from __future__ import annotations

import pygame

from earth_invasion.pygame_app.navigation import AppScreen

TEXT_COLOR = (230, 235, 255)
TITLE_COLOR = (255, 100, 45)
GAME_OVER_COLOR = (255, 70, 70)
GAME_CLEAR_COLOR = (100, 255, 160)


def draw_title_screen(
    surface: pygame.Surface,
    background: pygame.Surface,
    title_font: pygame.font.Font,
    text_font: pygame.font.Font,
) -> None:
    """タイトルと選択できる操作を描画する。"""

    _draw_menu_background(surface, background)
    _draw_centered_text(surface, title_font, "EARTH INVASION", 135, TITLE_COLOR)
    _draw_centered_text(surface, text_font, "Invade Earth and defeat its defenses", 195)
    _draw_centered_lines(
        surface,
        text_font,
        (
            "Enter: Start Game",
            "R: Rules",
            "Esc: Close",
        ),
        start_y=285,
        spacing=42,
    )


def draw_rules_screen(
    surface: pygame.Surface,
    background: pygame.Surface,
    title_font: pygame.font.Font,
    text_font: pygame.font.Font,
) -> None:
    """ゲームの目標と操作を描画する。"""

    _draw_menu_background(surface, background)
    _draw_centered_text(surface, title_font, "RULES", 65, TITLE_COLOR)
    _draw_centered_lines(
        surface,
        text_font,
        (
            "Up / Down: Move the UFO",
            "Z: Fire the beam",
            "Destroy enemies to fill the invasion gauge",
            "Avoid enemies and red projectiles",
            "Defeat the Earth Defense Boss to clear the game",
            "Enter / Esc: Return to Title",
        ),
        start_y=135,
        spacing=48,
    )


def draw_result_screen(
    surface: pygame.Surface,
    background: pygame.Surface,
    title_font: pygame.font.Font,
    text_font: pygame.font.Font,
    screen: AppScreen,
) -> None:
    """ゲームクリアまたはゲームオーバーの結果を描画する。"""

    if screen not in (AppScreen.GAME_OVER, AppScreen.GAME_CLEAR):
        raise ValueError("結果画面にはGAME_OVERまたはGAME_CLEARを指定してください")

    _draw_menu_background(surface, background)
    if screen is AppScreen.GAME_CLEAR:
        title = "MISSION COMPLETE"
        subtitle = "Earth's defenses have fallen"
        color = GAME_CLEAR_COLOR
    else:
        title = "MISSION FAILED"
        subtitle = "The invasion fleet was destroyed"
        color = GAME_OVER_COLOR

    _draw_centered_text(surface, title_font, title, 155, color)
    _draw_centered_text(surface, text_font, subtitle, 215)
    _draw_centered_lines(
        surface,
        text_font,
        (
            "R: Retry",
            "Enter / Esc: Return to Title",
        ),
        start_y=305,
        spacing=48,
    )


def _draw_menu_background(surface: pygame.Surface, background: pygame.Surface) -> None:
    surface.blit(background, (0, 0))
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 10, 175))
    surface.blit(overlay, (0, 0))


def _draw_centered_lines(
    surface: pygame.Surface,
    font: pygame.font.Font,
    lines: tuple[str, ...],
    *,
    start_y: int,
    spacing: int,
) -> None:
    for index, line in enumerate(lines):
        _draw_centered_text(surface, font, line, start_y + index * spacing)


def _draw_centered_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    center_y: int,
    color: tuple[int, int, int] = TEXT_COLOR,
) -> None:
    rendered = font.render(text, True, color)
    rectangle = rendered.get_rect(center=(surface.get_width() // 2, center_y))
    surface.blit(rendered, rectangle)
