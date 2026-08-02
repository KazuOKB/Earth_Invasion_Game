"""新しいPygameアプリケーションの土台。"""

from __future__ import annotations

import pygame

from earth_invasion.configuration import ApplicationConfig
from earth_invasion.pygame_app.display import Size, calculate_viewport

BACKGROUND_COLOR = (6, 10, 28)
LETTERBOX_COLOR = (0, 0, 0)
TITLE_COLOR = (255, 90, 30)
TEXT_COLOR = (230, 235, 255)


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
            title_font = pygame.font.Font(None, 64)
            text_font = pygame.font.Font(None, 30)
            clock = pygame.time.Clock()

            running = True
            frame_count = 0

            while running:
                for event in pygame.event.get():
                    close_requested = event.type == pygame.QUIT or (
                        event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                    )

                    if close_requested:
                        running = False
                    elif event.type == pygame.VIDEORESIZE:
                        window = pygame.display.set_mode(event.size, pygame.RESIZABLE)

                self._draw_start_screen(logical_surface, title_font, text_font)
                self._present(window, logical_surface)
                pygame.display.flip()

                frame_count += 1
                if frame_limit is not None and frame_count >= frame_limit:
                    running = False

                clock.tick(self.config.gameplay.updates_per_second)

            return 0
        finally:
            pygame.quit()

    def _draw_start_screen(
        self,
        surface: pygame.Surface,
        title_font: pygame.font.Font,
        text_font: pygame.font.Font,
    ) -> None:
        surface.fill(BACKGROUND_COLOR)

        title = title_font.render("Earth Invasion", True, TITLE_COLOR)
        title_rect = title.get_rect(center=(self.logical_size[0] // 2, 170))
        surface.blit(title, title_rect)

        profile = text_font.render(
            f"Stage profile: {self.config.stage.profile}",
            True,
            TEXT_COLOR,
        )
        profile_rect = profile.get_rect(center=(self.logical_size[0] // 2, 250))
        surface.blit(profile, profile_rect)

        guide = text_font.render("Press Esc to close", True, TEXT_COLOR)
        guide_rect = guide.get_rect(center=(self.logical_size[0] // 2, 300))
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
