"""Pygameアプリケーションの実行ループ。"""

from __future__ import annotations

import pygame

from earth_invasion.configuration import ApplicationConfig
from earth_invasion.gameplay.session import GameSession
from earth_invasion.pygame_app.assets import GameImages, load_game_images
from earth_invasion.pygame_app.audio import AudioPlayer
from earth_invasion.pygame_app.display import Size, calculate_viewport
from earth_invasion.pygame_app.effects import DamageFlash
from earth_invasion.pygame_app.fixed_step import FixedTimeStep
from earth_invasion.pygame_app.game_renderer import GameplayRenderer
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
from earth_invasion.pygame_app.session_factory import create_game_session
from earth_invasion.pygame_app.volume import VolumeControl, VolumeKey, VolumeTarget

LETTERBOX_COLOR = (0, 0, 0)


class PygameApplication:
    """ウィンドウ、イベント、更新、画面切り替えを管理する。"""

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
            return self._run_loop(frame_limit)
        finally:
            pygame.quit()

    def _run_loop(self, frame_limit: int | None) -> int:
        window = pygame.display.set_mode(self.logical_size, pygame.RESIZABLE)
        pygame.display.set_caption("Earth Invasion Game")
        logical_surface = pygame.Surface(self.logical_size)
        images = load_game_images(self.logical_size)
        session = create_game_session(self.config, images)
        renderer = GameplayRenderer(self.logical_size, self.config.stage.profile)
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
            window, running = self._handle_events(
                window,
                screen_flow,
                session,
                fixed_time_step,
                damage_flash,
                volume_control,
                audio_player,
                music_player,
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
                renderer,
                damage_flash,
                volume_control,
            )
            self._present(window, logical_surface)
            pygame.display.flip()

            frame_count += 1
            if frame_limit is not None and frame_count >= frame_limit:
                running = False

        return 0

    def _handle_events(
        self,
        window: pygame.Surface,
        screen_flow: ScreenFlow,
        session: GameSession,
        fixed_time_step: FixedTimeStep,
        damage_flash: DamageFlash,
        volume_control: VolumeControl,
        audio_player: AudioPlayer,
        music_player: MusicPlayer,
    ) -> tuple[pygame.Surface, bool]:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return window, False
            if event.type == pygame.VIDEORESIZE:
                window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                continue
            if event.type != pygame.KEYDOWN:
                continue
            if self._adjust_volume(
                event.key,
                screen_flow,
                volume_control,
                audio_player,
                music_player,
            ):
                continue

            action = action_for_key(screen_flow.current, _navigation_key(event.key))
            if not self._apply_navigation_action(
                action,
                screen_flow,
                session,
                fixed_time_step,
                damage_flash,
            ):
                return window, False

        return window, True

    def _adjust_volume(
        self,
        key: int,
        screen_flow: ScreenFlow,
        volume_control: VolumeControl,
        audio_player: AudioPlayer,
        music_player: MusicPlayer,
    ) -> bool:
        if screen_flow.current is not AppScreen.TITLE:
            return False

        volume_key = _volume_key(key)
        if not volume_control.handle(volume_key):
            return False

        audio_player.set_volume(volume_control.sound_effect_volume)
        music_player.set_volume(volume_control.music_volume)
        if volume_control.selected is VolumeTarget.SOUND_EFFECTS and volume_key in (
            VolumeKey.LEFT,
            VolumeKey.RIGHT,
        ):
            audio_player.play_preview()
        return True

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

        for _ in range(fixed_time_step.consume(elapsed_seconds)):
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
        renderer: GameplayRenderer,
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
                draw_rules_screen(surface, images.background, title_font, text_font)
            case AppScreen.GAMEPLAY:
                renderer.draw(surface, text_font, session, images, damage_flash)
            case AppScreen.GAME_OVER | AppScreen.GAME_CLEAR:
                draw_result_screen(
                    surface,
                    images.background,
                    title_font,
                    text_font,
                    screen_flow.current,
                )

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
