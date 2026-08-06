"""ブラウザ版の待機画面テンプレートを確認するテスト。"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]
TEMPLATE_PATH = PROJECT_ROOT / "web" / "earth-invasion.tmpl"


def test_browser_template_has_visible_loading_message() -> None:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    assert 'id="infobox" role="status" aria-live="polite"' in template
    assert 'id="loading-title">侵略準備中' in template
    assert 'id="loading-status">ゲームを読み込んでいます…' in template


def test_browser_template_has_ready_state() -> None:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    assert "function set_loading_state(message, ready)" in template
    assert "画面をクリックしてゲームを始めてください" in template
    assert 'style.display = "none"' in template
