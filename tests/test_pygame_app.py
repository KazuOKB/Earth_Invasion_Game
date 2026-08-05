"""Pygameアプリケーションの最小起動テスト。"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pygame
import pytest

from earth_invasion.configuration import load_application_config
from earth_invasion.gameplay.session import GameSession
from earth_invasion.gameplay.status import GameStatus
from earth_invasion.pygame_app.audio import AudioPlayer
from earth_invasion.pygame_app.effects import DamageFlash
from earth_invasion.pygame_app.fixed_step import FixedTimeStep
from earth_invasion.pygame_app.navigation import AppScreen


def test_application_runs_one_frame(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    text_input_was_stopped = False

    def remember_text_input_stop() -> None:
        nonlocal text_input_was_stopped
        text_input_was_stopped = True

    monkeypatch.setattr(pygame.key, "stop_text_input", remember_text_input_stop)

    from earth_invasion.pygame_app.app import PygameApplication

    app = PygameApplication(
        load_application_config("test"),
        ranking_path=tmp_path / "ranking.json",
    )

    assert app.run(frame_limit=1) == 0
    assert text_input_was_stopped


def test_application_async_api_runs_one_frame(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")

    from earth_invasion.pygame_app.app import PygameApplication

    app = PygameApplication(
        load_application_config("test"),
        ranking_path=tmp_path / "ranking.json",
    )

    assert asyncio.run(app.run_async(frame_limit=1)) == 0


def test_test_profile_result_is_saved_to_ranking(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    ranking_path = tmp_path / "ranking.json"
    event_was_sent = False
    result_score: int | None = None

    def start_game_once() -> list[pygame.event.Event]:
        nonlocal event_was_sent
        if event_was_sent:
            return []
        event_was_sent = True
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]

    monkeypatch.setattr(pygame.event, "get", start_game_once)

    from earth_invasion.pygame_app import app as app_module
    from earth_invasion.pygame_app.app import PygameApplication

    def finish_game_with_score(
        application: PygameApplication,
        session: GameSession,
        fixed_time_step: FixedTimeStep,
        audio_player: AudioPlayer,
        damage_flash: DamageFlash,
        elapsed_seconds: float,
    ) -> None:
        del application, fixed_time_step, audio_player, damage_flash, elapsed_seconds
        session.score = 500
        session.status = GameStatus.GAME_OVER

    monkeypatch.setattr(PygameApplication, "_update_gameplay", finish_game_with_score)

    def remember_result_score(
        surface: pygame.Surface,
        background: pygame.Surface,
        title_font: pygame.font.Font,
        text_font: pygame.font.Font,
        screen: AppScreen,
        score: int,
        ranking_scores: tuple[int, ...],
    ) -> None:
        nonlocal result_score
        del surface, background, title_font, text_font, screen, ranking_scores
        result_score = score

    monkeypatch.setattr(app_module, "draw_result_screen", remember_result_score)
    app = PygameApplication(
        load_application_config("test"),
        ranking_path=ranking_path,
    )

    assert app.run(frame_limit=1) == 0
    assert result_score == 500
    assert json.loads(ranking_path.read_text(encoding="utf-8")) == [500]
