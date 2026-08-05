"""設定と画像からゲームセッションを作れることを確認する。"""

from __future__ import annotations

import random

import pygame

from earth_invasion.configuration import load_application_config
from earth_invasion.pygame_app.assets import GameImages
from earth_invasion.pygame_app.session_factory import create_game_session


def test_session_uses_config_and_image_sizes() -> None:
    config = load_application_config("normal")
    images = _create_images()
    random_source = random.Random(1)

    session = create_game_session(config, images, random_source)

    assert (session.world_width, session.world_height) == (750, 500)
    assert (session.player_settings.width, session.player_settings.height) == (48, 32)
    assert (session.meteor_settings.width, session.meteor_settings.height) == (30, 28)
    assert session.stage.schedule.meteor_duration_seconds == 20.0
    assert session.invasion_settings.target == 100
    assert session.score_settings.clear_bonus == 2000
    assert session.boss_settings.max_health == 12
    assert session.random_source is random_source


def _create_images() -> GameImages:
    return GameImages(
        background=pygame.Surface((750, 500)),
        player=pygame.Surface((48, 32)),
        meteor=pygame.Surface((30, 28)),
        chaser=pygame.Surface((40, 36)),
        shooter=pygame.Surface((60, 40)),
        boss=pygame.Surface((90, 72)),
    )
