"""タイトル、ルール、結果画面の描画。"""

from __future__ import annotations

import pygame

from earth_invasion.pygame_app.navigation import AppScreen
from earth_invasion.pygame_app.volume import VolumeControl, VolumeTarget

TEXT_COLOR = (230, 235, 255)
TITLE_COLOR = (255, 100, 45)
GAME_OVER_COLOR = (255, 70, 70)
GAME_CLEAR_COLOR = (100, 255, 160)


def draw_title_screen(
    surface: pygame.Surface,
    background: pygame.Surface,
    title_font: pygame.font.Font,
    text_font: pygame.font.Font,
    volume_control: VolumeControl,
    ranking_scores: tuple[int, ...],
) -> None:
    """タイトルと選択できる操作を描画する。"""

    _draw_menu_background(surface, background)
    _draw_centered_text(surface, title_font, "EARTH INVASION", 60, TITLE_COLOR)
    _draw_centered_text(surface, text_font, "Invade Earth and defeat its defenses", 110)
    _draw_lines_at_x(
        surface,
        text_font,
        (
            "Enter: Start Game",
            "R: Rules",
            "Esc: Close",
        ),
        center_x=190,
        start_y=160,
        spacing=34,
    )
    _draw_ranking(surface, text_font, ranking_scores, center_x=555, start_y=145)
    _draw_centered_text(surface, text_font, "AUDIO", 300, TITLE_COLOR)
    _draw_volume_row(surface, text_font, volume_control, VolumeTarget.MUSIC, "BGM", 335)
    _draw_volume_row(
        surface,
        text_font,
        volume_control,
        VolumeTarget.SOUND_EFFECTS,
        "Effects",
        370,
    )
    _draw_centered_text(surface, text_font, "Up / Down: Select    Left / Right: Volume", 420)


def draw_rules_screen(
    surface: pygame.Surface,
    background: pygame.Surface,
    title_font: pygame.font.Font,
    text_font: pygame.font.Font,
) -> None:
    """ゲームの目標と操作を描画する。"""

    _draw_menu_background(surface, background)
    _draw_centered_text(surface, title_font, "RULES", 65, TITLE_COLOR)
    _draw_rule_rows(
        surface,
        text_font,
        (
            ("MOVE", "Up / Down: Move the UFO"),
            ("ATTACK", "Z: Fire the beam"),
            ("GAUGE", "Destroy enemies to fill the invasion gauge"),
            ("DAMAGE", "Avoid enemies and red projectiles"),
            ("GOAL", "Defeat the Earth Defense Boss"),
            ("RETURN", "Enter / Esc: Return to Title"),
        ),
        label_x=120,
        description_x=230,
        start_y=135,
        spacing=48,
    )


def draw_result_screen(
    surface: pygame.Surface,
    background: pygame.Surface,
    title_font: pygame.font.Font,
    text_font: pygame.font.Font,
    screen: AppScreen,
    score: int,
    ranking_scores: tuple[int, ...],
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

    _draw_centered_text(surface, title_font, title, 85, color)
    _draw_centered_text(surface, text_font, subtitle, 135)
    _draw_centered_text(surface, title_font, f"SCORE: {score}", 190)
    _draw_ranking(
        surface, text_font, ranking_scores, center_x=surface.get_width() // 2, start_y=230
    )
    _draw_centered_lines(
        surface,
        text_font,
        (
            "R: Retry",
            "Enter / Esc: Return to Title",
        ),
        start_y=415,
        spacing=36,
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


def _draw_rule_rows(
    surface: pygame.Surface,
    font: pygame.font.Font,
    rows: tuple[tuple[str, str], ...],
    *,
    label_x: int,
    description_x: int,
    start_y: int,
    spacing: int,
) -> None:
    for index, (label, description) in enumerate(rows):
        center_y = start_y + index * spacing
        label_text = font.render(label, True, TITLE_COLOR)
        description_text = font.render(description, True, TEXT_COLOR)
        surface.blit(label_text, label_text.get_rect(midleft=(label_x, center_y)))
        surface.blit(
            description_text,
            description_text.get_rect(midleft=(description_x, center_y)),
        )


def _draw_lines_at_x(
    surface: pygame.Surface,
    font: pygame.font.Font,
    lines: tuple[str, ...],
    *,
    center_x: int,
    start_y: int,
    spacing: int,
) -> None:
    for index, line in enumerate(lines):
        _draw_text_at_x(surface, font, line, center_x, start_y + index * spacing)


def _draw_ranking(
    surface: pygame.Surface,
    font: pygame.font.Font,
    scores: tuple[int, ...],
    *,
    center_x: int,
    start_y: int,
) -> None:
    _draw_text_at_x(surface, font, "TOP 5", center_x, start_y, TITLE_COLOR)
    for index in range(5):
        score_text = "---" if index >= len(scores) else str(scores[index])
        _draw_text_at_x(
            surface,
            font,
            f"{index + 1}. {score_text}",
            center_x,
            start_y + 30 + index * 25,
        )


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


def _draw_text_at_x(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    center_x: int,
    center_y: int,
    color: tuple[int, int, int] = TEXT_COLOR,
) -> None:
    rendered = font.render(text, True, color)
    surface.blit(rendered, rendered.get_rect(center=(center_x, center_y)))


def _draw_volume_row(
    surface: pygame.Surface,
    font: pygame.font.Font,
    volume_control: VolumeControl,
    target: VolumeTarget,
    label: str,
    center_y: int,
) -> None:
    prefix = ">" if volume_control.selected is target else " "
    percentage = volume_control.percentage_for(target)
    color = TITLE_COLOR if volume_control.selected is target else TEXT_COLOR
    _draw_centered_text(surface, font, f"{prefix} {label}: {percentage}%", center_y, color)
