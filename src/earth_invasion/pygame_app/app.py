"""新しいPygameアプリケーションの土台。"""

from __future__ import annotations

import random

import pygame

from earth_invasion.configuration import ApplicationConfig
from earth_invasion.gameplay.session import GameSession
from earth_invasion.gameplay.settings import (
    ChaserSettings,
    InvasionSettings,
    MeteorSettings,
    PlayerSettings,
    WeaponSettings,
)
from earth_invasion.gameplay.stage import StageSchedule
from earth_invasion.pygame_app.assets import (
    load_chaser_image,
    load_meteor_image,
    load_player_image,
)
from earth_invasion.pygame_app.display import Size, calculate_viewport
from earth_invasion.pygame_app.fixed_step import FixedTimeStep
from earth_invasion.pygame_app.input import create_player_command

BACKGROUND_COLOR = (6, 10, 28)
LETTERBOX_COLOR = (0, 0, 0)
TITLE_COLOR = (255, 90, 30)
TEXT_COLOR = (230, 235, 255)
GAME_OVER_COLOR = (255, 70, 70)
BEAM_COLOR = (100, 235, 255)
GAUGE_COLOR = (255, 100, 40)
GAUGE_BACKGROUND_COLOR = (45, 50, 70)
GAUGE_WIDTH = 250
GAUGE_HEIGHT = 14
PLAYER_BLINK_INTERVAL_SECONDS = 0.1


class PygameApplication:
    """ウィンドウ、イベント、描画の流れを管理する。"""

    def __init__(self, config: ApplicationConfig) -> None:
        self.config = config
        resolution = config.gameplay.logical_resolution
        self.logical_size: Size = (resolution.width, resolution.height)

    def run(self, frame_limit: int | None = None) -> int:
        """アプリケーションを実行する。"""

        if frame_limit is not None and frame_limit <= 0:
            raise ValueError("frame_limitは0より大きくしてください")

        pygame.display.init()
        pygame.font.init()

        try:
            window = pygame.display.set_mode(self.logical_size, pygame.RESIZABLE)
            pygame.display.set_caption("Earth Invasion Game")
            logical_surface = pygame.Surface(self.logical_size)
            player_image = load_player_image()
            meteor_image = load_meteor_image()
            chaser_image = load_chaser_image()
            session = self._create_session(
                player_image.get_size(),
                meteor_image.get_size(),
                chaser_image.get_size(),
            )
            fixed_time_step = FixedTimeStep(self.config.gameplay.updates_per_second)
            title_font = pygame.font.Font(None, 48)
            text_font = pygame.font.Font(None, 30)
            clock = pygame.time.Clock()

            running = True
            frame_count = 0

            while running:
                elapsed_seconds = clock.tick(self.config.gameplay.updates_per_second) / 1000.0

                for event in pygame.event.get():
                    close_requested = event.type == pygame.QUIT or (
                        event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                    )

                    if close_requested:
                        running = False
                    elif (
                        event.type == pygame.KEYDOWN
                        and event.key == pygame.K_r
                        and session.is_game_over
                    ):
                        session.restart()
                    elif event.type == pygame.VIDEORESIZE:
                        window = pygame.display.set_mode(event.size, pygame.RESIZABLE)

                if not running:
                    break

                keys = pygame.key.get_pressed()
                command = create_player_command(
                    up_pressed=keys[pygame.K_UP],
                    down_pressed=keys[pygame.K_DOWN],
                    fire_pressed=keys[pygame.K_z],
                )
                update_count = fixed_time_step.consume(elapsed_seconds)

                for _ in range(update_count):
                    session.update(command, fixed_time_step.step_seconds)

                self._draw_gameplay_preview(
                    logical_surface,
                    title_font,
                    text_font,
                    session,
                    player_image,
                    meteor_image,
                    chaser_image,
                )
                self._present(window, logical_surface)
                pygame.display.flip()

                frame_count += 1
                if frame_limit is not None and frame_count >= frame_limit:
                    running = False

            return 0
        finally:
            pygame.quit()

    def _create_session(
        self,
        player_size: Size,
        meteor_size: Size,
        chaser_size: Size,
    ) -> GameSession:
        player_width, player_height = player_size
        meteor_width, meteor_height = meteor_size
        chaser_width, chaser_height = chaser_size
        player_config = self.config.gameplay.player
        weapon_config = self.config.gameplay.weapon
        meteor_config = self.config.gameplay.meteor
        chaser_config = self.config.gameplay.chaser
        invasion_rewards = self.config.gameplay.invasion_rewards
        stage_config = self.config.stage
        return GameSession.create(
            world_width=self.logical_size[0],
            world_height=self.logical_size[1],
            player_settings=PlayerSettings(
                width=player_width,
                height=player_height,
                movement_speed=player_config.movement_speed_pixels_per_second,
                max_health=player_config.max_health,
                invincibility_seconds=player_config.invincibility_seconds,
            ),
            weapon_settings=WeaponSettings(
                beam_speed=weapon_config.beam_speed_pixels_per_second,
                beam_cooldown_seconds=weapon_config.beam_cooldown_seconds,
            ),
            meteor_settings=MeteorSettings(
                width=meteor_width,
                height=meteor_height,
                spawn_interval_seconds=meteor_config.spawn_interval_seconds,
                minimum_speed=meteor_config.minimum_speed_pixels_per_second,
                maximum_speed=meteor_config.maximum_speed_pixels_per_second,
            ),
            chaser_settings=ChaserSettings(
                width=chaser_width,
                height=chaser_height,
                spawn_interval_seconds=chaser_config.spawn_interval_seconds,
                horizontal_speed=chaser_config.horizontal_speed_pixels_per_second,
                tracking_speed=chaser_config.tracking_speed_pixels_per_second,
            ),
            invasion_settings=InvasionSettings(
                target=stage_config.invasion_target,
                meteor_reward=invasion_rewards.meteor,
                chaser_reward=invasion_rewards.chaser,
            ),
            stage_schedule=StageSchedule(
                meteor_duration_seconds=stage_config.duration_seconds_for("meteor"),
                chaser_duration_seconds=stage_config.duration_seconds_for("chaser"),
                shooter_duration_seconds=stage_config.duration_seconds_for("shooter"),
            ),
            random_source=random.Random(),
        )

    def _draw_gameplay_preview(
        self,
        surface: pygame.Surface,
        title_font: pygame.font.Font,
        text_font: pygame.font.Font,
        session: GameSession,
        player_image: pygame.Surface,
        meteor_image: pygame.Surface,
        chaser_image: pygame.Surface,
    ) -> None:
        surface.fill(BACKGROUND_COLOR)

        title = title_font.render("Earth Invasion", True, TITLE_COLOR)
        title_rect = title.get_rect(center=(self.logical_size[0] // 2, 40))
        surface.blit(title, title_rect)

        remaining_seconds = session.stage.remaining_seconds
        remaining_text = "no limit" if remaining_seconds is None else f"{remaining_seconds:.1f}s"
        stage_status = text_font.render(
            f"Profile: {self.config.stage.profile}    "
            f"Phase: {session.current_phase.value}    Time: {remaining_text}",
            True,
            TEXT_COLOR,
        )
        stage_status_rect = stage_status.get_rect(center=(self.logical_size[0] // 2, 78))
        surface.blit(stage_status, stage_status_rect)

        self._draw_invasion_gauge(surface, text_font, session)
        self._draw_health(surface, text_font, session)

        for meteor in session.meteors:
            meteor_position = round(meteor.x), round(meteor.y)
            surface.blit(meteor_image, meteor_position)

        for chaser in session.chasers:
            chaser_position = round(chaser.x), round(chaser.y)
            surface.blit(chaser_image, chaser_position)

        if self._player_is_visible(session):
            player_position = round(session.player.x), round(session.player.y)
            surface.blit(player_image, player_position)

        for beam in session.beams:
            beam_rectangle = pygame.Rect(
                round(beam.x),
                round(beam.y),
                beam.width,
                beam.height,
            )
            pygame.draw.rect(surface, BEAM_COLOR, beam_rectangle)

        guide = text_font.render("Up / Down: Move    Z: Beam    Esc: Close", True, TEXT_COLOR)
        guide_rect = guide.get_rect(center=(self.logical_size[0] // 2, 475))
        surface.blit(guide, guide_rect)

        if session.is_game_over:
            self._draw_game_over(surface, title_font, text_font)

    def _draw_invasion_gauge(
        self,
        surface: pygame.Surface,
        text_font: pygame.font.Font,
        session: GameSession,
    ) -> None:
        gauge_x = (self.logical_size[0] - GAUGE_WIDTH) // 2
        gauge_y = 105
        invasion_target = session.invasion_settings.target
        gauge_ratio = session.invasion_gauge / invasion_target
        filled_width = round(GAUGE_WIDTH * gauge_ratio)

        background = pygame.Rect(gauge_x, gauge_y, GAUGE_WIDTH, GAUGE_HEIGHT)
        filled = pygame.Rect(gauge_x, gauge_y, filled_width, GAUGE_HEIGHT)
        pygame.draw.rect(surface, GAUGE_BACKGROUND_COLOR, background)
        pygame.draw.rect(surface, GAUGE_COLOR, filled)

        label = text_font.render(
            f"Invasion: {session.invasion_gauge} / {invasion_target}",
            True,
            TEXT_COLOR,
        )
        label_rect = label.get_rect(center=(self.logical_size[0] // 2, 137))
        surface.blit(label, label_rect)

    def _draw_health(
        self,
        surface: pygame.Surface,
        text_font: pygame.font.Font,
        session: GameSession,
    ) -> None:
        health = text_font.render(
            f"Health: {session.player.health} / {session.player_settings.max_health}",
            True,
            TEXT_COLOR,
        )
        surface.blit(health, (20, 105))

    def _player_is_visible(self, session: GameSession) -> bool:
        if not session.player.is_invincible:
            return True

        blink_count = int(session.player.invincibility_remaining / PLAYER_BLINK_INTERVAL_SECONDS)
        return blink_count % 2 == 0

    def _draw_game_over(
        self,
        surface: pygame.Surface,
        title_font: pygame.font.Font,
        text_font: pygame.font.Font,
    ) -> None:
        overlay = pygame.Surface(self.logical_size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        title = title_font.render("GAME OVER", True, GAME_OVER_COLOR)
        title_rect = title.get_rect(center=(self.logical_size[0] // 2, 220))
        surface.blit(title, title_rect)

        guide = text_font.render("R: Retry    Esc: Close", True, TEXT_COLOR)
        guide_rect = guide.get_rect(center=(self.logical_size[0] // 2, 270))
        surface.blit(guide, guide_rect)

    def _present(
        self,
        window: pygame.Surface,
        logical_surface: pygame.Surface,
    ) -> None:
        window.fill(LETTERBOX_COLOR)
        viewport = calculate_viewport(self.logical_size, window.get_size())
        scaled_surface = pygame.transform.smoothscale(logical_surface, viewport.size)
        window.blit(scaled_surface, (viewport.x, viewport.y))
