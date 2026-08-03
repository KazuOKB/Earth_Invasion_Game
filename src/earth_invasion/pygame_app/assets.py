"""Pythonパッケージに含まれる画像を読み込む。"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from io import BytesIO

import pygame

ASSET_PACKAGE = "earth_invasion.assets"
SHOOTER_IMAGE_SIZE = (60, 40)


@dataclass(frozen=True, slots=True)
class GameImages:
    """1回の起動で使う画像をまとめる。"""

    background: pygame.Surface
    player: pygame.Surface
    meteor: pygame.Surface
    chaser: pygame.Surface
    shooter: pygame.Surface
    boss: pygame.Surface


def load_game_images(size: tuple[int, int]) -> GameImages:
    """ゲームで使う画像をすべて読み込む。"""

    return GameImages(
        background=load_background_image(size),
        player=load_player_image(),
        meteor=load_meteor_image(),
        chaser=load_chaser_image(),
        shooter=load_shooter_image(),
        boss=load_boss_image(),
    )


def load_player_image() -> pygame.Surface:
    """プレイヤーのUFO画像を読み込む。"""

    return _load_image("ufo003.png")


def load_meteor_image() -> pygame.Surface:
    """隕石画像を読み込む。"""

    return _load_image("meteo2.png")


def load_chaser_image() -> pygame.Surface:
    """追尾敵の画像を読み込む。"""

    return _load_image("chaser.png")


def load_shooter_image() -> pygame.Surface:
    """攻撃敵のUFO画像を読み込み、ゲーム用の大きさへ縮小する。"""

    return pygame.transform.smoothscale(_load_image("shooter.png"), SHOOTER_IMAGE_SIZE)


def load_boss_image() -> pygame.Surface:
    """地球防衛ボスの画像を読み込む。"""

    return _load_image("boss.png")


def load_background_image(size: tuple[int, int]) -> pygame.Surface:
    """宇宙背景を内部画面の大きさで読み込む。"""

    return pygame.transform.smoothscale(_load_image("background.png"), size)


def _load_image(filename: str) -> pygame.Surface:
    resource = files(ASSET_PACKAGE).joinpath(filename)
    image_data = BytesIO(resource.read_bytes())
    return pygame.image.load(image_data, filename).convert_alpha()
