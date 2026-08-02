"""Pythonパッケージに含まれる画像を読み込む。"""

from __future__ import annotations

from importlib.resources import files
from io import BytesIO

import pygame

ASSET_PACKAGE = "earth_invasion.assets"


def load_player_image() -> pygame.Surface:
    """プレイヤーのUFO画像を読み込む。"""

    resource = files(ASSET_PACKAGE).joinpath("ufo003.png")
    image_data = BytesIO(resource.read_bytes())
    return pygame.image.load(image_data, "ufo003.png").convert_alpha()
