"""新しいPygameアプリケーションの土台。"""

from __future__ import annotations

import random

import pygame

from earth_invasion.configuration import ApplicationConfig
from earth_invasion.gameplay.session import GameSession
from earth_invasion.gameplay.settings import (
    BossSettings,
    ChaserSettings,
    InvasionSettings,
    MeteorSettings,
    PlayerSettings,
    ShooterSettings,
    WeaponSettings,
)
from earth_invasion.gameplay.stage import StageSchedule
from earth_invasion.pygame_app.assets import (
    load_background_image,
    load_boss_image,
    load_chaser_image,
    load_meteor_image,
    load_player_image,
    load_shooter_image,
)
from earth_invasion.pygame_app.display import Size, calculate_viewport
from earth_invasion.pygame_app.fixed_step import FixedTimeStep
from earth_invasion.pygame_app.hud import HUD_HEIGHT, heart_states
from earth_invasion.pygame_app.input import create_player_command

LETTERBOX_COLOR = (0, 0, 0)
TEXT_COLOR = (230, 235, 255)
HUD_COLOR = (6, 10, 28)
HUD_BORDER_COLOR = (80, 100, 145)
GAME_OVER_COLOR = (255, 70, 70)
GAME_CLEAR_COLOR = (100, 255, 160)
BEAM_COLOR = (100, 235, 255)
ENEMY_PROJECTILE_COLOR = (255, 80, 80)
GAUGE_COLOR = (255, 100, 40)
GAUGE_BACKGROUND_COLOR = (45, 50, 70)
GAUGE_WIDTH = 250
GAUGE_HEIGHT = 14
BOSS_HEALTH_WIDTH = 220
BOSS_HEALTH_HEIGHT = 12
HEART_COLOR = (245, 70, 90)
EMPTY_HEART_COLOR = (85, 90, 110)
HEART_SIZE = 20
HEART_SPACING = 7
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
            background_image = load_background_image(self.logical_size)
            player_image = load_player_image()
            meteor_image = load_meteor_image()
            chaser_image = load_chaser_image()
            shooter_image = load_shooter_image()
            boss_image = load_boss_image()
            session = self._create_session(
                player_image.get_size(),
                meteor_image.get_size(),
                chaser_image.get_size(),
                shooter_image.get_size(),
                boss_image.get_size(),
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
                        and session.is_finished
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
                    background_image,
                    player_image,
                    meteor_image,
                    chaser_image,
                    shooter_image,
                    boss_image,
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
        shooter_size: Size,
        boss_size: Size,
    ) -> GameSession:
        player_width, player_height = player_size
        meteor_width, meteor_height = meteor_size
        chaser_width, chaser_height = chaser_size
        shooter_width, shooter_height = shooter_size
        boss_width, boss_height = boss_size
        player_config = self.config.gameplay.player
        weapon_config = self.config.gameplay.weapon
        meteor_config = self.config.gameplay.meteor
        chaser_config = self.config.gameplay.chaser
        shooter_config = self.config.gameplay.shooter
        boss_config = self.config.gameplay.boss
        invasion_rewards = self.config.gameplay.invasion_rewards
        stage_config = self.config.stage
        return GameSession.create(
            world_width=self.logical_size[0],
            world_height=self.logical_size[1],
            playfield_top=HUD_HEIGHT,
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
            shooter_settings=ShooterSettings(
                width=shooter_width,
                height=shooter_height,
                spawn_interval_seconds=shooter_config.spawn_interval_seconds,
                horizontal_speed=shooter_config.horizontal_speed_pixels_per_second,
                shot_interval_seconds=shooter_config.shot_interval_seconds,
                projectile_speed=shooter_config.projectile_speed_pixels_per_second,
            ),
            boss_settings=BossSettings(
                width=boss_width,
                height=boss_height,
                max_health=boss_config.max_health,
                vertical_speed=boss_config.vertical_speed_pixels_per_second,
                shot_interval_seconds=boss_config.shot_interval_seconds,
                projectile_speed=boss_config.projectile_speed_pixels_per_second,
            ),
            invasion_settings=InvasionSettings(
                target=stage_config.invasion_target,
                meteor_reward=invasion_rewards.meteor,
                chaser_reward=invasion_rewards.chaser,
                shooter_reward=invasion_rewards.shooter,
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
        background_image: pygame.Surface,
        player_image: pygame.Surface,
        meteor_image: pygame.Surface,
        chaser_image: pygame.Surface,
        shooter_image: pygame.Surface,
        boss_image: pygame.Surface,
    ) -> None:
        surface.blit(background_image, (0, 0))

        for meteor in session.meteors:
            meteor_position = round(meteor.x), round(meteor.y)
            surface.blit(meteor_image, meteor_position)

        for chaser in session.chasers:
            chaser_position = round(chaser.x), round(chaser.y)
            surface.blit(chaser_image, chaser_position)

        for shooter in session.shooters:
            shooter_position = round(shooter.x), round(shooter.y)
            surface.blit(shooter_image, shooter_position)

        if session.boss is not None:
            boss_position = round(session.boss.x), round(session.boss.y)
            surface.blit(boss_image, boss_position)

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

        for projectile in session.enemy_projectiles:
            projectile_rectangle = pygame.Rect(
                round(projectile.x),
                round(projectile.y),
                projectile.width,
                projectile.height,
            )
            pygame.draw.rect(surface, ENEMY_PROJECTILE_COLOR, projectile_rectangle)

        self._draw_hud(surface, text_font, session)

        if session.is_game_over:
            self._draw_game_over(surface, title_font, text_font)
        elif session.is_game_clear:
            self._draw_game_clear(surface, title_font, text_font)

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
            f"Profile: {self.config.stage.profile}    "
            f"Phase: {session.current_phase.value}    Time: {remaining_text}",
            True,
            TEXT_COLOR,
        )
        stage_status_rect = stage_status.get_rect(center=(self.logical_size[0] // 2, 18))
        surface.blit(stage_status, stage_status_rect)

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
        gauge_y = 44
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
        label_rect = label.get_rect(center=(self.logical_size[0] // 2, 78))
        surface.blit(label, label_rect)

    def _draw_hearts(
        self,
        surface: pygame.Surface,
        text_font: pygame.font.Font,
        session: GameSession,
    ) -> None:
        label = text_font.render("LIFE", True, TEXT_COLOR)
        surface.blit(label, (20, 51))

        for index, is_filled in enumerate(
            heart_states(session.player.health, session.player_settings.max_health)
        ):
            heart_x = 75 + index * (HEART_SIZE + HEART_SPACING)
            self._draw_heart(surface, heart_x, 50, is_filled)

    def _draw_heart(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        is_filled: bool,
    ) -> None:
        radius = HEART_SIZE // 4
        left_center = (x + radius + 2, y + radius + 2)
        right_center = (x + HEART_SIZE - radius - 2, y + radius + 2)
        body_points = [
            (x + 1, y + radius + 2),
            (x + HEART_SIZE - 1, y + radius + 2),
            (x + HEART_SIZE // 2, y + HEART_SIZE),
        ]

        if is_filled:
            pygame.draw.circle(surface, HEART_COLOR, left_center, radius)
            pygame.draw.circle(surface, HEART_COLOR, right_center, radius)
            pygame.draw.polygon(surface, HEART_COLOR, body_points)
            return

        pygame.draw.circle(surface, EMPTY_HEART_COLOR, left_center, radius, width=2)
        pygame.draw.circle(surface, EMPTY_HEART_COLOR, right_center, radius, width=2)
        pygame.draw.polygon(surface, EMPTY_HEART_COLOR, body_points, width=2)

    def _draw_boss_health(
        self,
        surface: pygame.Surface,
        text_font: pygame.font.Font,
        session: GameSession,
    ) -> None:
        if session.boss is None:
            return

        gauge_x = self.logical_size[0] - BOSS_HEALTH_WIDTH - 20
        gauge_y = 65
        health_ratio = session.boss.health / session.boss_settings.max_health
        filled_width = round(BOSS_HEALTH_WIDTH * health_ratio)
        background = pygame.Rect(
            gauge_x,
            gauge_y,
            BOSS_HEALTH_WIDTH,
            BOSS_HEALTH_HEIGHT,
        )
        filled = pygame.Rect(gauge_x, gauge_y, filled_width, BOSS_HEALTH_HEIGHT)
        pygame.draw.rect(surface, GAUGE_BACKGROUND_COLOR, background)
        pygame.draw.rect(surface, GAME_OVER_COLOR, filled)

        label = text_font.render(
            f"Boss: {session.boss.health} / {session.boss_settings.max_health}",
            True,
            TEXT_COLOR,
        )
        label_rect = label.get_rect(center=(gauge_x + BOSS_HEALTH_WIDTH // 2, 47))
        surface.blit(label, label_rect)

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

    def _draw_game_clear(
        self,
        surface: pygame.Surface,
        title_font: pygame.font.Font,
        text_font: pygame.font.Font,
    ) -> None:
        overlay = pygame.Surface(self.logical_size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        title = title_font.render("MISSION COMPLETE", True, GAME_CLEAR_COLOR)
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
