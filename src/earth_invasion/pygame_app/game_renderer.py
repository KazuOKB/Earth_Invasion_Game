"""ゲームプレイ画面の描画。"""

from __future__ import annotations

import pygame

from earth_invasion.gameplay.session import GameSession
from earth_invasion.pygame_app.assets import GameImages
from earth_invasion.pygame_app.display import Size
from earth_invasion.pygame_app.effects import DamageFlash
from earth_invasion.pygame_app.hud import HUD_HEIGHT, heart_states

TEXT_COLOR = (230, 235, 255)
HUD_COLOR = (6, 10, 28)
HUD_BORDER_COLOR = (80, 100, 145)
BEAM_COLOR = (100, 235, 255)
ENEMY_PROJECTILE_COLOR = (255, 80, 80)
GAUGE_COLOR = (255, 100, 40)
GAUGE_BACKGROUND_COLOR = (45, 50, 70)
BOSS_HEALTH_COLOR = (255, 70, 70)
HEART_COLOR = (245, 70, 90)
EMPTY_HEART_COLOR = (85, 90, 110)
DAMAGE_FLASH_COLOR = (255, 35, 35)

GAUGE_WIDTH = 250
GAUGE_HEIGHT = 14
BOSS_HEALTH_WIDTH = 220
BOSS_HEALTH_HEIGHT = 12
HEART_SIZE = 20
HEART_SPACING = 7
PLAYER_BLINK_INTERVAL_SECONDS = 0.1
DAMAGE_FLASH_MAX_ALPHA = 105


class GameplayRenderer:
    """ゲーム内の物体、被弾演出、HUDを描画する。"""

    def __init__(self, logical_size: Size, stage_profile: str) -> None:
        self.logical_size = logical_size
        self.stage_profile = stage_profile

    def draw(
        self,
        surface: pygame.Surface,
        text_font: pygame.font.Font,
        session: GameSession,
        images: GameImages,
        damage_flash: DamageFlash,
    ) -> None:
        """現在のゲーム状態を内部画面へ描画する。"""

        surface.blit(images.background, (0, 0))
        self._draw_enemies(surface, session, images)
        self._draw_player(surface, session, images.player)
        self._draw_projectiles(surface, session)
        self._draw_damage_flash(surface, damage_flash)
        self._draw_hud(surface, text_font, session)

    def _draw_enemies(
        self,
        surface: pygame.Surface,
        session: GameSession,
        images: GameImages,
    ) -> None:
        for meteor in session.meteors:
            surface.blit(images.meteor, (round(meteor.x), round(meteor.y)))

        for chaser in session.chasers:
            surface.blit(images.chaser, (round(chaser.x), round(chaser.y)))

        for shooter in session.shooters:
            surface.blit(images.shooter, (round(shooter.x), round(shooter.y)))

        if session.boss is not None:
            surface.blit(images.boss, (round(session.boss.x), round(session.boss.y)))

    def _draw_player(
        self,
        surface: pygame.Surface,
        session: GameSession,
        player_image: pygame.Surface,
    ) -> None:
        if not _player_is_visible(session):
            return

        surface.blit(player_image, (round(session.player.x), round(session.player.y)))

    def _draw_projectiles(self, surface: pygame.Surface, session: GameSession) -> None:
        for beam in session.beams:
            rectangle = pygame.Rect(round(beam.x), round(beam.y), beam.width, beam.height)
            pygame.draw.rect(surface, BEAM_COLOR, rectangle)

        for projectile in session.enemy_projectiles:
            rectangle = pygame.Rect(
                round(projectile.x),
                round(projectile.y),
                projectile.width,
                projectile.height,
            )
            pygame.draw.rect(surface, ENEMY_PROJECTILE_COLOR, rectangle)

    def _draw_damage_flash(
        self,
        surface: pygame.Surface,
        damage_flash: DamageFlash,
    ) -> None:
        if not damage_flash.is_visible:
            return

        overlay_size = self.logical_size[0], self.logical_size[1] - HUD_HEIGHT
        overlay = pygame.Surface(overlay_size, pygame.SRCALPHA)
        alpha = round(DAMAGE_FLASH_MAX_ALPHA * damage_flash.intensity)
        overlay.fill((*DAMAGE_FLASH_COLOR, alpha))
        surface.blit(overlay, (0, HUD_HEIGHT))

    def _draw_hud(
        self,
        surface: pygame.Surface,
        text_font: pygame.font.Font,
        session: GameSession,
    ) -> None:
        panel = pygame.Rect(0, 0, self.logical_size[0], HUD_HEIGHT)
        pygame.draw.rect(surface, HUD_COLOR, panel)
        pygame.draw.line(
            surface,
            HUD_BORDER_COLOR,
            (0, HUD_HEIGHT - 1),
            (self.logical_size[0], HUD_HEIGHT - 1),
            width=2,
        )

        remaining_seconds = session.stage.remaining_seconds
        remaining_text = "no limit" if remaining_seconds is None else f"{remaining_seconds:.1f}s"
        stage_status = text_font.render(
            f"Profile: {self.stage_profile}    "
            f"Phase: {session.current_phase.value}    Time: {remaining_text}",
            True,
            TEXT_COLOR,
        )
        stage_status_rect = stage_status.get_rect(midleft=(20, 18))
        surface.blit(stage_status, stage_status_rect)

        score = text_font.render(f"Score: {session.score}", True, TEXT_COLOR)
        score_rect = score.get_rect(midright=(self.logical_size[0] - 20, 18))
        surface.blit(score, score_rect)

        self._draw_invasion_gauge(surface, text_font, session)
        self._draw_hearts(surface, text_font, session)
        self._draw_boss_health(surface, text_font, session)

    def _draw_invasion_gauge(
        self,
        surface: pygame.Surface,
        text_font: pygame.font.Font,
        session: GameSession,
    ) -> None:
        gauge_x = (self.logical_size[0] - GAUGE_WIDTH) // 2
        invasion_target = session.invasion_settings.target
        filled_width = round(GAUGE_WIDTH * session.invasion_gauge / invasion_target)

        background = pygame.Rect(gauge_x, 44, GAUGE_WIDTH, GAUGE_HEIGHT)
        filled = pygame.Rect(gauge_x, 44, filled_width, GAUGE_HEIGHT)
        pygame.draw.rect(surface, GAUGE_BACKGROUND_COLOR, background)
        pygame.draw.rect(surface, GAUGE_COLOR, filled)

        label = text_font.render(
            f"Invasion: {session.invasion_gauge} / {invasion_target}",
            True,
            TEXT_COLOR,
        )
        surface.blit(label, label.get_rect(center=(self.logical_size[0] // 2, 78)))

    def _draw_hearts(
        self,
        surface: pygame.Surface,
        text_font: pygame.font.Font,
        session: GameSession,
    ) -> None:
        surface.blit(text_font.render("LIFE", True, TEXT_COLOR), (20, 51))

        states = heart_states(session.player.health, session.player_settings.max_health)
        for index, is_filled in enumerate(states):
            heart_x = 75 + index * (HEART_SIZE + HEART_SPACING)
            _draw_heart(surface, heart_x, 50, is_filled)

    def _draw_boss_health(
        self,
        surface: pygame.Surface,
        text_font: pygame.font.Font,
        session: GameSession,
    ) -> None:
        if session.boss is None:
            return

        gauge_x = self.logical_size[0] - BOSS_HEALTH_WIDTH - 20
        health_ratio = session.boss.health / session.boss_settings.max_health
        filled_width = round(BOSS_HEALTH_WIDTH * health_ratio)
        background = pygame.Rect(gauge_x, 65, BOSS_HEALTH_WIDTH, BOSS_HEALTH_HEIGHT)
        filled = pygame.Rect(gauge_x, 65, filled_width, BOSS_HEALTH_HEIGHT)
        pygame.draw.rect(surface, GAUGE_BACKGROUND_COLOR, background)
        pygame.draw.rect(surface, BOSS_HEALTH_COLOR, filled)

        label = text_font.render(
            f"Boss: {session.boss.health} / {session.boss_settings.max_health}",
            True,
            TEXT_COLOR,
        )
        label_center = gauge_x + BOSS_HEALTH_WIDTH // 2, 47
        surface.blit(label, label.get_rect(center=label_center))


def _draw_heart(surface: pygame.Surface, x: int, y: int, is_filled: bool) -> None:
    radius = HEART_SIZE // 4
    left_center = (x + radius + 2, y + radius + 2)
    right_center = (x + HEART_SIZE - radius - 2, y + radius + 2)
    body_points = [
        (x + 1, y + radius + 2),
        (x + HEART_SIZE - 1, y + radius + 2),
        (x + HEART_SIZE // 2, y + HEART_SIZE),
    ]
    color = HEART_COLOR if is_filled else EMPTY_HEART_COLOR
    width = 0 if is_filled else 2

    pygame.draw.circle(surface, color, left_center, radius, width=width)
    pygame.draw.circle(surface, color, right_center, radius, width=width)
    pygame.draw.polygon(surface, color, body_points, width=width)


def _player_is_visible(session: GameSession) -> bool:
    if not session.player.is_invincible:
        return True

    blink_count = int(session.player.invincibility_remaining / PLAYER_BLINK_INTERVAL_SECONDS)
    return blink_count % 2 == 0
