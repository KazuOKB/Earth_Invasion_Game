"""ゲームプレイ画面の描画を確認する。"""

from __future__ import annotations

import pygame

from earth_invasion.configuration import load_application_config
from earth_invasion.pygame_app.assets import GameImages
from earth_invasion.pygame_app.effects import DamageFlash
from earth_invasion.pygame_app.game_renderer import HUD_COLOR, GameplayRenderer
from earth_invasion.pygame_app.hud import HUD_HEIGHT
from earth_invasion.pygame_app.session_factory import create_game_session


def test_gameplay_renderer_draws_hud_over_background() -> None:
    pygame.font.init()
    try:
        images = _create_images()
        session = create_game_session(load_application_config("normal"), images)
        renderer = GameplayRenderer((750, 500), "normal")
        surface = pygame.Surface((750, 500))
        text_font = pygame.font.Font(None, 30)

        renderer.draw(surface, text_font, session, images, DamageFlash())

        assert surface.get_at((0, 0))[:3] == HUD_COLOR
        assert surface.get_at((0, HUD_HEIGHT + 1))[:3] == (1, 2, 3)
    finally:
        pygame.font.quit()


def _create_images() -> GameImages:
    background = pygame.Surface((750, 500))
    background.fill((1, 2, 3))
    return GameImages(
        background=background,
        player=pygame.Surface((48, 32)),
        meteor=pygame.Surface((30, 28)),
        chaser=pygame.Surface((40, 36)),
        shooter=pygame.Surface((60, 40)),
        boss=pygame.Surface((90, 72)),
    )
