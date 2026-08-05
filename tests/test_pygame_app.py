"""Pygameアプリケーションの最小起動テスト。"""

from __future__ import annotations

from pathlib import Path

import pygame
import pytest

from earth_invasion.configuration import load_application_config


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
