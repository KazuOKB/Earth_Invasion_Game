"""Pythonパッケージに含まれる画像を読み込む。"""

from __future__ import annotations

from importlib.resources import files
from io import BytesIO

import pygame

ASSET_PACKAGE = "earth_invasion.assets"


def load_player_image() -> pygame.Surface:
    """プレイヤーのUFO画像を読み込む。"""

    return _load_image("ufo003.png")


def load_meteor_image() -> pygame.Surface:
    """隕石画像を読み込む。"""

    return _load_image("meteo2.png")


def load_chaser_image() -> pygame.Surface:
    """追尾敵の画像を読み込む。"""

    return _load_image("chaser.png")


def _load_image(filename: str) -> pygame.Surface:
    resource = files(ASSET_PACKAGE).joinpath(filename)
    image_data = BytesIO(resource.read_bytes())
    return pygame.image.load(image_data, filename).convert_alpha()
