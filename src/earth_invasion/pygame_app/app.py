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
from earth_invasion.pygame_app.assets import GameImages, load_game_images
from earth_invasion.pygame_app.audio import AudioPlayer
from earth_invasion.pygame_app.display import Size, calculate_viewport
from earth_invasion.pygame_app.effects import DamageFlash
from earth_invasion.pygame_app.fixed_step import FixedTimeStep
from earth_invasion.pygame_app.hud import HUD_HEIGHT, heart_states
from earth_invasion.pygame_app.input import create_player_command
from earth_invasion.pygame_app.music import MusicPlayer, music_track_for
from earth_invasion.pygame_app.navigation import (
    AppScreen,
    NavigationAction,
    NavigationKey,
    ScreenFlow,
    action_for_key,
)
from earth_invasion.pygame_app.screens import (
    draw_result_screen,
    draw_rules_screen,
    draw_title_screen,
)
from earth_invasion.pygame_app.volume import VolumeControl, VolumeKey, VolumeTarget

LETTERBOX_COLOR = (0, 0, 0)
TEXT_COLOR = (230, 235, 255)
HUD_COLOR = (6, 10, 28)
HUD_BORDER_COLOR = (80, 100, 145)
BEAM_COLOR = (100, 235, 255)
ENEMY_PROJECTILE_COLOR = (255, 80, 80)
GAUGE_COLOR = (255, 100, 40)
GAUGE_BACKGROUND_COLOR = (45, 50, 70)
BOSS_HEALTH_COLOR = (255, 70, 70)
GAUGE_WIDTH = 250
GAUGE_HEIGHT = 14
BOSS_HEALTH_WIDTH = 220
BOSS_HEALTH_HEIGHT = 12
HEART_COLOR = (245, 70, 90)
EMPTY_HEART_COLOR = (85, 90, 110)
HEART_SIZE = 20
HEART_SPACING = 7
PLAYER_BLINK_INTERVAL_SECONDS = 0.1
DAMAGE_FLASH_COLOR = (255, 35, 35)
DAMAGE_FLASH_MAX_ALPHA = 105


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
            images = load_game_images(self.logical_size)
            session = self._create_session(images)
            fixed_time_step = FixedTimeStep(self.config.gameplay.updates_per_second)
            screen_flow = ScreenFlow()
            audio_config = self.config.gameplay.audio
            audio_player = AudioPlayer.create(audio_config.sound_effect_volume)
            music_player = MusicPlayer.create(audio_config.music_volume)
            volume_control = VolumeControl(
                music_volume=audio_config.music_volume,
                sound_effect_volume=audio_config.sound_effect_volume,
            )
            damage_flash = DamageFlash()
            menu_title_font = pygame.font.Font(None, 72)
            title_font = pygame.font.Font(None, 48)
            text_font = pygame.font.Font(None, 30)
            clock = pygame.time.Clock()

            running = True
            frame_count = 0

            while running:
                elapsed_seconds = clock.tick(self.config.gameplay.updates_per_second) / 1000.0

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.VIDEORESIZE:
                        window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                    elif event.type == pygame.KEYDOWN:
                        volume_key = _volume_key(event.key)
                        if screen_flow.current is AppScreen.TITLE and volume_control.handle(
                            volume_key
                        ):
                            audio_player.set_volume(volume_control.sound_effect_volume)
                            music_player.set_volume(volume_control.music_volume)
                            if (
                                volume_control.selected is VolumeTarget.SOUND_EFFECTS
                                and volume_key in (VolumeKey.LEFT, VolumeKey.RIGHT)
                            ):
                                audio_player.play_preview()
                            continue

                        action = action_for_key(
                            screen_flow.current,
                            _navigation_key(event.key),
                        )
                        running = running and self._apply_navigation_action(
                            action,
                            screen_flow,
                            session,
                            fixed_time_step,
                            damage_flash,
                        )

                if not running:
                    break

                if screen_flow.current is AppScreen.GAMEPLAY:
                    self._update_gameplay(
                        session,
                        fixed_time_step,
                        audio_player,
                        damage_flash,
                        elapsed_seconds,
                    )
                    screen_flow.show_gameplay_result(session.status)

                music_player.play(music_track_for(screen_flow.current, session.current_phase))
                self._draw_current_screen(
                    logical_surface,
                    menu_title_font,
                    title_font,
                    text_font,
                    screen_flow,
                    session,
                    images,
                    damage_flash,
                    volume_control,
                )
                self._present(window, logical_surface)
                pygame.display.flip()

                frame_count += 1
                if frame_limit is not None and frame_count >= frame_limit:
                    running = False

            return 0
        finally:
            pygame.quit()

    def _apply_navigation_action(
        self,
        action: NavigationAction,
        screen_flow: ScreenFlow,
        session: GameSession,
        fixed_time_step: FixedTimeStep,
        damage_flash: DamageFlash,
    ) -> bool:
        if action is NavigationAction.CLOSE:
            return False

        if action in (NavigationAction.START_GAME, NavigationAction.RETRY):
            session.restart()

        if action is not NavigationAction.NONE:
            fixed_time_step.reset()
            damage_flash.reset()
            screen_flow.apply(action)

        return True

    def _update_gameplay(
        self,
        session: GameSession,
        fixed_time_step: FixedTimeStep,
        audio_player: AudioPlayer,
        damage_flash: DamageFlash,
        elapsed_seconds: float,
    ) -> None:
        damage_flash.update(elapsed_seconds)
        keys = pygame.key.get_pressed()
        command = create_player_command(
            up_pressed=keys[pygame.K_UP],
            down_pressed=keys[pygame.K_DOWN],
            fire_pressed=keys[pygame.K_z],
        )
        update_count = fixed_time_step.consume(elapsed_seconds)

        for _ in range(update_count):
            events = session.update(command, fixed_time_step.step_seconds)
            audio_player.play(events)
            if events.player_was_hit:
                damage_flash.trigger()

    def _draw_current_screen(
        self,
        surface: pygame.Surface,
        menu_title_font: pygame.font.Font,
        title_font: pygame.font.Font,
        text_font: pygame.font.Font,
        screen_flow: ScreenFlow,
        session: GameSession,
        images: GameImages,
        damage_flash: DamageFlash,
        volume_control: VolumeControl,
    ) -> None:
        match screen_flow.current:
            case AppScreen.TITLE:
                draw_title_screen(
                    surface,
                    images.background,
                    menu_title_font,
                    text_font,
                    volume_control,
                )
            case AppScreen.RULES:
                draw_rules_screen(
                    surface,
                    images.background,
                    title_font,
                    text_font,
                )
            case AppScreen.GAMEPLAY:
                self._draw_gameplay_preview(
                    surface,
                    text_font,
                    session,
                    images,
                    damage_flash,
                )
            case AppScreen.GAME_OVER | AppScreen.GAME_CLEAR:
                draw_result_screen(
                    surface,
                    images.background,
                    title_font,
                    text_font,
                    screen_flow.current,
                )

    def _create_session(
        self,
        images: GameImages,
    ) -> GameSession:
        player_width, player_height = images.player.get_size()
        meteor_width, meteor_height = images.meteor.get_size()
        chaser_width, chaser_height = images.chaser.get_size()
        shooter_width, shooter_height = images.shooter.get_size()
        boss_width, boss_height = images.boss.get_size()
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
        text_font: pygame.font.Font,
        session: GameSession,
        images: GameImages,
        damage_flash: DamageFlash,
    ) -> None:
        surface.blit(images.background, (0, 0))

        for meteor in session.meteors:
            meteor_position = round(meteor.x), round(meteor.y)
            surface.blit(images.meteor, meteor_position)

        for chaser in session.chasers:
            chaser_position = round(chaser.x), round(chaser.y)
            surface.blit(images.chaser, chaser_position)

        for shooter in session.shooters:
            shooter_position = round(shooter.x), round(shooter.y)
            surface.blit(images.shooter, shooter_position)

        if session.boss is not None:
            boss_position = round(session.boss.x), round(session.boss.y)
            surface.blit(images.boss, boss_position)

        if self._player_is_visible(session):
            player_position = round(session.player.x), round(session.player.y)
            surface.blit(images.player, player_position)

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

        self._draw_damage_flash(surface, damage_flash)
        self._draw_hud(surface, text_font, session)

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
        pygame.draw.rect(surface, BOSS_HEALTH_COLOR, filled)

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

    def _present(
        self,
        window: pygame.Surface,
        logical_surface: pygame.Surface,
    ) -> None:
        window.fill(LETTERBOX_COLOR)
        viewport = calculate_viewport(self.logical_size, window.get_size())
        scaled_surface = pygame.transform.smoothscale(logical_surface, viewport.size)
        window.blit(scaled_surface, (viewport.x, viewport.y))


def _navigation_key(key: int) -> NavigationKey:
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        return NavigationKey.ENTER
    if key == pygame.K_r:
        return NavigationKey.R
    if key == pygame.K_ESCAPE:
        return NavigationKey.ESCAPE
    return NavigationKey.OTHER


def _volume_key(key: int) -> VolumeKey:
    if key == pygame.K_UP:
        return VolumeKey.UP
    if key == pygame.K_DOWN:
        return VolumeKey.DOWN
    if key == pygame.K_LEFT:
        return VolumeKey.LEFT
    if key == pygame.K_RIGHT:
        return VolumeKey.RIGHT
    return VolumeKey.OTHER
