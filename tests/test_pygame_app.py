"""Pygameアプリケーションの最小起動テスト。"""

from __future__ import annotations

import pytest

from earth_invasion.configuration import load_application_config


def test_application_runs_one_frame(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")

    from earth_invasion.pygame_app.app import PygameApplication

    app = PygameApplication(load_application_config("test"))

    assert app.run(frame_limit=1) == 0
