"""コマンドライン起動処理のテスト。"""

from __future__ import annotations

import pytest

from earth_invasion.__main__ import main


def test_main_prints_test_profile(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["--stage-profile", "test", "--check-config"])

    output = capsys.readouterr()
    assert exit_code == 0
    assert "設定: test" in output.out
    assert "侵略ゲージ目標: 10" in output.out
