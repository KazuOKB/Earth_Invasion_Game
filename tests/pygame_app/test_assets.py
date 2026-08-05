"""画像の読み込み時に行う色加工を確認する。"""

from __future__ import annotations

import pygame

from earth_invasion.pygame_app.assets import SHOOTER_TINT, _tint_image


def test_enemy_tint_changes_rgb_and_keeps_alpha() -> None:
    image = pygame.Surface((1, 1), pygame.SRCALPHA)
    image.fill((255, 255, 255, 128))

    tinted = _tint_image(image, SHOOTER_TINT)

    color = tinted.get_at((0, 0))
    assert (color.r, color.g, color.b, color.a) == (*SHOOTER_TINT, 128)
